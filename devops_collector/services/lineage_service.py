"""DBT 数据血缘解析与渲染服务"""

import json
import logging
import os


logger = logging.getLogger(__name__)


class LineageService:
    """提供 DBT 物理血缘解析服务。"""

    @classmethod
    def generate_mermaid_lineage(cls, manifest_path: str = "dbt_project/target/manifest.json") -> str:
        """读取 manifest.json，解析依赖并输出 Mermaid 格式文本。"""
        if not os.path.exists(manifest_path):
            logger.warning(f"DBT manifest.json not found at: {manifest_path}")
            return "graph LR\n    error[manifest.json not found, please run dbt build first]"

        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = json.load(f)

            nodes = data.get("nodes", {})
            sources = data.get("sources", {})

            # 节点翻译与定义字典
            node_labels = {}
            # 依赖线集合，去重
            edges = set()

            # 1. 扫描所有 sources
            for s_key, s_val in sources.items():
                s_name = f"{s_val.get('source_name')}.{s_val.get('name')}"
                node_labels[s_key] = s_name

            # 2. 扫描所有 nodes (models)
            for n_key, n_val in nodes.items():
                n_name = n_val.get("name")
                node_labels[n_key] = n_name

                # 提取依赖关系
                depends = n_val.get("depends_on", {}).get("nodes", [])
                for dep in depends:
                    # 仅保留我们关心的 source 和 model 关系
                    if dep in node_labels or dep.startswith("source.") or dep.startswith("model."):
                        edges.add((dep, n_key))

            # 3. 生成 Mermaid 语句
            lines = ["graph LR"]

            # 为每个节点生成合法的标识符 (Mermaid 节点 id 不能有点号，替换为双下划线)
            def clean_id(raw_id: str) -> str:
                return raw_id.replace(".", "__").replace("-", "_")

            # 记录已渲染的节点定义，避免重复渲染
            rendered_nodes = set()

            # 先输出关系线
            for parent, child in sorted(edges):
                p_id = clean_id(parent)
                c_id = clean_id(child)

                # 获取友好 label
                p_label = node_labels.get(parent, parent.split(".")[-1])
                c_label = node_labels.get(child, child.split(".")[-1])

                # 渲染节点样式/名称定义
                if parent not in rendered_nodes:
                    lines.append(f'    {p_id}["{p_label}"]')
                    rendered_nodes.add(parent)
                if child not in rendered_nodes:
                    lines.append(f'    {c_id}["{c_label}"]')
                    rendered_nodes.add(child)

                lines.append(f"    {p_id} --> {c_id}")

            if len(lines) == 1:
                return "graph LR\n    empty[No models or dependencies found]"

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Failed to generate Mermaid lineage: {e}")
            return f"graph LR\n    error[Failed to parse lineage: {str(e)}]"
