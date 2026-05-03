"""GitLab Worker Merge Request Mixin.

提供 MR 及其相关分析逻辑。
"""

import logging
from datetime import UTC

from devops_collector.core.utils import parse_iso8601

from ..models import GitLabMergeRequest, GitLabProject


logger = logging.getLogger(__name__)


class MergeRequestMixin:
    """提供 MR 相关的同步逻辑。

    包含 MR 的基础信息同步、数据转换以及深度协作分析功能。
    """

    def _sync_merge_requests(self, project: GitLabProject, since: str | None) -> int:
        """从项目同步合并请求 (MR)。

        Args:
            project (GitLabProject): 关联的项目实体。
            since (Optional[str]): ISO 格式时间字符串，仅同步该时间后的 MR。

        Returns:
            int: 同步处理的 MR 总数。
        """
        return self._process_generator(
            self.client.get_project_merge_requests(project.id, since=since),
            lambda batch: self._save_mrs_batch(project, batch),
        )

    def _save_mrs_batch(self, project: GitLabProject, batch: list[dict]) -> None:
        """批量保存合并请求记录。

        第一阶段：Extract & Load (Staging) - 原始数据落盘 (COPY FROM 批量)
        第二阶段：Transform & Load (DW) - 业务逻辑解析

        Args:
            project (GitLabProject): 关联的项目实体。
            batch (List[dict]): 包含多个 MR 原始数据的列表。
        """
        self.bulk_save_to_staging("gitlab", "merge_request", batch)
        self._transform_mrs_batch(project, batch)

    def _transform_mrs_batch(self, project: GitLabProject, batch: list[dict]) -> None:
        """核心解析逻辑：将原始 JSON 转换为 MergeRequest 模型。

        Args:
            project (GitLabProject): 关联的项目实体。
            batch (List[dict]): 包含多个 MR 原始数据的列表。
        """
        ids = [item["id"] for item in batch]
        existing = self.session.query(GitLabMergeRequest).filter(GitLabMergeRequest.id.in_(ids)).all()
        existing_map = {m.id: m for m in existing}
        for data in batch:
            mr = existing_map.get(data["id"])
            if not mr:
                mr = GitLabMergeRequest(id=data["id"])
                self.session.add(mr)
            mr.project_id = project.id
            mr.iid = data["iid"]
            mr.title = data["title"]
            mr.description = data.get("description")
            mr.state = data["state"]
            mr.is_draft = data.get("draft", False)
            mr.author_username = data.get("username") or data.get("author", {}).get("username")
            mr.created_at = parse_iso8601(data["created_at"])

            # 初始化 Draft 追踪
            if mr.is_draft and not mr.draft_at:
                mr.draft_at = mr.created_at

            mr.updated_at = parse_iso8601(data["updated_at"])
            mr.merge_commit_sha = data.get("merge_commit_sha")
            if data.get("merged_at"):
                mr.merged_at = parse_iso8601(data["merged_at"])
            if data.get("closed_at"):
                mr.closed_at = parse_iso8601(data["closed_at"])
            if data.get("author"):
                if self.user_resolver:
                    uid = self.user_resolver.resolve(data["author"]["id"])
                    mr.author_id = uid
            if hasattr(self, "_apply_traceability_extraction"):
                self._apply_traceability_extraction(mr)
            if self.enable_deep_analysis or mr.state in ("merged", "opened"):
                if hasattr(self, "client"):
                    self._apply_mr_collaboration_analysis(project, mr)

    def _apply_mr_collaboration_analysis(self, project: GitLabProject, mr: GitLabMergeRequest) -> None:
        """分析合并请求的协作深度与评审质量。

        此方法会调用多个 API 端点以获取审批、评论和流水线信息，
        用于计算 Review Cycles, First Response Time 等效能指标。

        Args:
            project (GitLabProject): 关联的项目实体。
            mr (GitLabMergeRequest): 要分析的合并请求对象。
        """
        try:
            approvals = self.client.get_mr_approvals(project.id, mr.iid)
            mr.approval_count = len(approvals.get("approved_by", []))
            notes = list(self.client.get_mr_notes(project.id, mr.iid))
            human_notes = [n for n in notes if n.get("system") is False]
            mr.human_comment_count = len(human_notes)
            if human_notes:
                human_notes.sort(key=lambda x: x["created_at"])
                first_note_at = parse_iso8601(human_notes[0]["created_at"])
                mr.first_response_at = first_note_at
            system_notes = [n for n in notes if n.get("system") is True]

            # --- VSM 深度分析 (Touch/Wait Time) ---
            self._analyze_vsm_metrics(project, mr, notes)

            # --- Review 深度指标提取 (Collaboration Quality) ---
            self._analyze_review_quality(mr, human_notes, system_notes)

            updated_commits_notes = [n for n in system_notes if "added" in n.get("body", "").lower() and "commit" in n.get("body", "").lower()]
            mr.review_cycles = 1 + len(updated_commits_notes)
            if mr.merged_at and mr.created_at:
                delta = mr.merged_at - mr.created_at
                mr.review_time_total = int(delta.total_seconds())
            pipelines = self.client.get_mr_pipelines(project.id, mr.iid)
            if pipelines:
                latest_p = pipelines[0]
                mr.quality_gate_status = "passed" if latest_p.get("status") == "success" else "failed"

        except Exception as e:
            logger.warning(f"Failed to analyze MR collaboration for {mr.iid}: {e}")

    def _analyze_vsm_metrics(self, project: GitLabProject, mr: GitLabMergeRequest, notes: list[dict]) -> None:
        """分析价值流指标。"""
        # 1. 识别 Ready 时间 (从 System Notes 中寻找 "marked as ready")
        if not mr.ready_at:
            ready_notes = [n for n in notes if n.get("system") and "marked as ready" in n.get("body", "").lower()]
            if ready_notes:
                ready_notes.sort(key=lambda x: x["created_at"])
                mr.ready_at = parse_iso8601(ready_notes[0]["created_at"])
                # 如果从 Note 中发现了 Ready 事件，且没有 draft_at，则补齐为创建时间
                if not mr.draft_at:
                    mr.draft_at = mr.created_at
            elif not mr.is_draft:
                # 如果目前不是 Draft 且没找到 ready 事件，则认为创建即 Ready
                mr.ready_at = mr.created_at

        # 2. 如果当前是 Draft 且没有 draft_at，则补齐
        if mr.is_draft and not mr.draft_at:
            mr.draft_at = mr.created_at
        if mr.ready_at and mr.draft_at:
            mr.draft_duration = int((mr.ready_at - mr.draft_at).total_seconds())

        if mr.first_response_at and mr.ready_at:
            delta = mr.first_response_at - mr.ready_at
            mr.wait_time_to_review = int(max(0, delta.total_seconds()))

        # 3. 同步状态流转事件
        self._sync_mr_state_transitions(project, mr)

    def _analyze_review_quality(self, mr: GitLabMergeRequest, human_notes: list[dict], system_notes: list[dict]) -> None:
        """评估评审质量与深度。"""
        # 1. 计算有效评论数 (引发了后续代码变更的评论)
        update_times = [parse_iso8601(n["created_at"]) for n in system_notes if "added" in n.get("body", "").lower() and "commit" in n.get("body", "").lower()]
        update_times.sort()

        effective_note_ids = set()
        for hn in human_notes:
            hn_time = parse_iso8601(hn["created_at"])
            # 寻找在该评论之后的第一个代码更新事件
            for ut in update_times:
                if ut > hn_time:
                    effective_note_ids.add(hn["id"])
                    break
        mr.effective_comment_count = len(effective_note_ids)

        # 2. 识别秒批 (Rubber-stamping)
        # 条件：评审时长 < 5 分钟 且 无人工评论
        approved_notes = [n for n in system_notes if "approved this merge request" in n.get("body", "").lower()]
        if approved_notes and mr.ready_at:
            approved_notes.sort(key=lambda x: x["created_at"])
            first_approval_at = parse_iso8601(approved_notes[0]["created_at"])

            # 统一时区进行比较
            start_time = mr.ready_at if mr.ready_at.tzinfo else mr.ready_at.replace(tzinfo=UTC)
            approval_time = first_approval_at if first_approval_at.tzinfo else first_approval_at.replace(tzinfo=UTC)

            delay_seconds = (approval_time - start_time).total_seconds()
            if delay_seconds < 300 and mr.human_comment_count == 0:
                mr.rubber_stamp = True
            else:
                mr.rubber_stamp = False

    def _sync_mr_state_transitions(self, project: GitLabProject, mr: GitLabMergeRequest) -> None:
        """同步并保存 MR 的状态流转。"""
        from ..models import GitLabMergeRequestStateTransition

        events = list(self.client.get_merge_request_state_events(project.id, mr.iid))
        events.sort(key=lambda x: x["created_at"])

        last_state = "opened"  # 初始状态
        last_time = mr.created_at

        # 清除旧记录重新计算（或者实现增量，这里为了保证计算准确性先采用覆盖式）
        self.session.query(GitLabMergeRequestStateTransition).filter_by(mr_id=mr.id).delete()

        for e in events:
            current_state = e["state"]
            current_time = parse_iso8601(e["created_at"])

            duration = (current_time - last_time).total_seconds()

            transition = GitLabMergeRequestStateTransition(
                mr_id=mr.id, from_state=last_state, to_state=current_state, timestamp=current_time, duration_hours=duration / 3600.0
            )
            self.session.add(transition)

            last_state = current_state
            last_time = current_time
