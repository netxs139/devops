# Service Desk API 接口实现

## 1. 业务方提交 Bug

@app.post("/service-desk/submit-bug")
async def submit_bug_via_service_desk(project_id: int, data: ServiceDeskBugSubmit):
"""业务方通过 Service Desk 提交缺陷。

```
Args:
    project_id: GitLab 项目 ID。
    data: Bug 提交数据。

Returns:
    dict: 包含追踪码和 GitLab Issue 链接。
"""
try:
    # 1. 生成追踪码
    tracking_code = f"BUG-{datetime.now().strftime('%Y%m%d')}-{len(SERVICE_DESK_TICKETS) + 1:03d}"
    
    # 2. 构造 GitLab Issue 描述
    description = f"""## 🐛 业务方缺陷报告 (Service Desk)
```

**报告人**: {data.requester_name} ({data.requester_email})\
**追踪码**: {tracking_code}

### 缺陷信息

- **严重程度**: {data.severity}
- **优先级**: {data.priority}
- **省份/地域**: {data.province}
- **环境**: {data.environment}

### 复现步骤

{data.steps_to_repro}

### 实际结果

{data.actual_result}

### 期望结果

{data.expected_result}

### 附件

{chr(10).join([f'- {att}' for att in data.attachments]) if data.attachments else '无'}

______________________________________________________________________

*此缺陷由业务方通过 Service Desk 提交，请及时处理并回复。*
"""

```
    # 3. 在 GitLab 创建 Issue
    url = f"{Config.GITLAB_URL}/api/v4/projects/{project_id}/issues"
    headers = {"PRIVATE-TOKEN": Config.GITLAB_PRIVATE_TOKEN}
    
    payload = {
        "title": f"[Service Desk] {data.title}",
        "description": description,
        "labels": f"type::bug,severity::{data.severity},priority::{data.priority},province::{data.province},origin::service-desk"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    issue_data = response.json()
    
    # 4. 保存工单记录
    ticket = {
        "tracking_code": tracking_code,
        "ticket_type": "bug",
        "status": "pending",
        "gitlab_issue_iid": issue_data.get("iid"),
        "gitlab_issue_url": issue_data.get("web_url"),
        "requester_name": data.requester_name,
        "requester_email": data.requester_email,
        "title": data.title,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    SERVICE_DESK_TICKETS[tracking_code] = ticket
    
    logger.info(f"Service Desk Bug created: {tracking_code} -> Issue #{issue_data.get('iid')}")
    
    return {
        "status": "success",
        "tracking_code": tracking_code,
        "gitlab_issue_iid": issue_data.get("iid"),
        "gitlab_issue_url": issue_data.get("web_url"),
        "message": f"缺陷已提交成功！追踪码: {tracking_code}，我们会尽快处理并通过邮件通知您。"
    }
    
except Exception as e:
    logger.error(f"Service Desk Bug submission failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## 2. 业务方提交需求

@app.post("/service-desk/submit-requirement")
async def submit_requirement_via_service_desk(project_id: int, data: ServiceDeskRequirementSubmit):
"""业务方通过 Service Desk 提交需求。

```
Args:
    project_id: GitLab 项目 ID。
    data: 需求提交数据。

Returns:
    dict: 包含追踪码和 GitLab Issue 链接。
"""
try:
    # 1. 生成追踪码
    tracking_code = f"REQ-{datetime.now().strftime('%Y%m%d')}-{len(SERVICE_DESK_TICKETS) + 1:03d}"
    
    # 2. 构造 GitLab Issue 描述
    description = f"""## 📋 业务方需求提交 (Service Desk)
```

**提交人**: {data.requester_name} ({data.requester_email})\
**追踪码**: {tracking_code}

### 需求信息

- **需求类型**: {data.req_type}
- **优先级**: {data.priority}
- **省份/地域**: {data.province}
- **期望交付时间**: {data.expected_delivery or '未指定'}

### 需求描述

{data.description}

______________________________________________________________________

*此需求由业务方通过 Service Desk 提交，请评审后进入开发流程。*
"""

```
    # 3. 在 GitLab 创建 Issue
    url = f"{Config.GITLAB_URL}/api/v4/projects/{project_id}/issues"
    headers = {"PRIVATE-TOKEN": Config.GITLAB_PRIVATE_TOKEN}
    
    payload = {
        "title": f"[Service Desk] {data.title}",
        "description": description,
        "labels": f"type::requirement,req-type::{data.req_type},priority::{data.priority},province::{data.province},origin::service-desk,review-state::draft"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    issue_data = response.json()
    
    # 4. 保存工单记录
    ticket = {
        "tracking_code": tracking_code,
        "ticket_type": "requirement",
        "status": "pending",
        "gitlab_issue_iid": issue_data.get("iid"),
        "gitlab_issue_url": issue_data.get("web_url"),
        "requester_name": data.requester_name,
        "requester_email": data.requester_email,
        "title": data.title,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    SERVICE_DESK_TICKETS[tracking_code] = ticket
    
    logger.info(f"Service Desk Requirement created: {tracking_code} -> Issue #{issue_data.get('iid')}")
    
    return {
        "status": "success",
        "tracking_code": tracking_code,
        "gitlab_issue_iid": issue_data.get("iid"),
        "gitlab_issue_url": issue_data.get("web_url"),
        "message": f"需求已提交成功！追踪码: {tracking_code}，我们会进行评审并通过邮件通知您。"
    }
    
except Exception as e:
    logger.error(f"Service Desk Requirement submission failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## 3. 查询工单状态

@app.get("/service-desk/track/{tracking_code}")
async def track_service_desk_ticket(tracking_code: str):
"""通过追踪码查询工单状态（无需登录）。

```
Args:
    tracking_code: 工单追踪码。

Returns:
    ServiceDeskTicket: 工单详情。
"""
if tracking_code not in SERVICE_DESK_TICKETS:
    raise HTTPException(status_code=404, detail="工单不存在，请检查追踪码是否正确")

ticket = SERVICE_DESK_TICKETS[tracking_code]

# 从 GitLab 获取最新状态
if ticket.get("gitlab_issue_iid"):
    try:
        # 提取 project_id (简化处理，实际应从 ticket 中存储)
        # 这里假设从 URL 中提取
        url_parts = ticket["gitlab_issue_url"].split("/")
        project_id = url_parts[url_parts.index("projects") + 1] if "projects" in url_parts else None
        
        if project_id:
            issue_url = f"{Config.GITLAB_URL}/api/v4/projects/{project_id}/issues/{ticket['gitlab_issue_iid']}"
            headers = {"PRIVATE-TOKEN": Config.GITLAB_PRIVATE_TOKEN}
            response = requests.get(issue_url, headers=headers)
            
            if response.status_code == 200:
                issue = response.json()
                # 更新状态
                if issue.get("state") == "closed":
                    ticket["status"] = "completed"
                elif "in-progress" in issue.get("labels", []):
                    ticket["status"] = "in-progress"
                
                ticket["updated_at"] = issue.get("updated_at", ticket["updated_at"])
    except Exception as e:
        logger.warning(f"Failed to sync ticket status from GitLab: {e}")

return ServiceDeskTicket(**ticket)
```

## 4. 获取所有工单列表

@app.get("/service-desk/tickets")
async def list_service_desk_tickets(email: Optional[str] = None):
"""获取 Service Desk 工单列表。

```
Args:
    email: 可选，按提交人邮箱过滤。

Returns:
    List[ServiceDeskTicket]: 工单列表。
"""
tickets = list(SERVICE_DESK_TICKETS.values())

if email:
    tickets = [t for t in tickets if t.get("requester_email") == email]

# 按创建时间倒序
tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)

return tickets
```
