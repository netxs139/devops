# Service Desk 访问方式说明

## 📋 当前实现方式

### ✅ **方式 1: Web 界面（无需登录）**

**访问地址**: http://your-server:8000/static/service_desk.html

**特点**:

- ✅ **无需登录** - 业务方直接访问即可使用
- ✅ **无需账号** - 不需要注册或创建账户
- ✅ **简单易用** - 填写表单即可提交
- ✅ **追踪码查询** - 通过追踪码查询工单状态

**使用流程**:

```
1. 业务方打开 Service Desk 主页
   ↓
2. 选择"提交 Bug"或"提交需求"
   ↓
3. 填写表单（包括姓名和邮箱）
   ↓
4. 提交后获得追踪码
   ↓
5. 使用追踪码查询工单状态
```

**优点**:

- 🚀 快速上手，无学习成本
- 🔓 无需管理账号和密码
- 📱 支持任何设备访问
- 🌐 可以分享链接给任何人

**缺点**:

- ⚠️ 无法自动识别用户身份
- ⚠️ 需要手动输入姓名和邮箱
- ⚠️ 无法查看"我的工单"列表（除非记住追踪码）

______________________________________________________________________

## 🔮 可选实现方式

### 方式 2: 邮件集成（推荐增强）

#### 2.1 接收邮件创建工单

**实现方案**: 监听专用邮箱，自动将邮件转换为工单

```python
# 示例实现
import imaplib
import email
from email.header import decode_header

def monitor_service_desk_email():
    """监听 Service Desk 邮箱，自动创建工单"""
    
    # 连接邮箱
    mail = imaplib.IMAP4_SSL("imap.example.com")
    mail.login("service-desk@example.com", "password")
    mail.select("INBOX")
    
    # 搜索未读邮件
    status, messages = mail.search(None, "UNSEEN")
    
    for msg_num in messages[0].split():
        # 获取邮件
        status, msg_data = mail.fetch(msg_num, "(RFC822)")
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)
        
        # 解析邮件
        subject = decode_header(email_message["Subject"])[0][0]
        from_email = email.utils.parseaddr(email_message["From"])[1]
        body = get_email_body(email_message)
        
        # 判断是 Bug 还是需求（根据主题关键词）
        if "[Bug]" in subject or "缺陷" in subject:
            create_bug_from_email(from_email, subject, body)
        elif "[需求]" in subject or "Requirement" in subject:
            create_requirement_from_email(from_email, subject, body)
```

**邮件格式示例**:

```
收件人: service-desk@example.com
主题: [Bug] 登录页面无法显示

严重程度: S2
优先级: P2
环境: production
省份: 广东

复现步骤:
1. 打开登录页面
2. 输入用户名密码
3. 点击登录

实际结果: 页面空白
期望结果: 正常跳转
```

**优点**:

- 📧 业务方使用熟悉的邮件工具
- 🔄 自动创建工单
- 📨 自动回复追踪码

**缺点**:

- 🔧 需要配置邮箱服务器
- 📝 邮件格式需要规范
- ⚙️ 需要额外的邮件解析逻辑

______________________________________________________________________

#### 2.2 邮件通知（推荐优先实现）

**实现方案**: 工单状态变更时自动发送邮件通知

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_ticket_notification(ticket, event_type):
    """发送工单通知邮件
    
    Args:
        ticket: 工单信息
        event_type: 事件类型（created, updated, completed）
    """
    
    # 配置 SMTP
    smtp_server = "smtp.example.com"
    smtp_port = 587
    sender_email = "service-desk@example.com"
    sender_password = "password"
    
    # 构造邮件
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Service Desk] 工单 {ticket['tracking_code']} - {event_type}"
    msg["From"] = sender_email
    msg["To"] = ticket['requester_email']
    
    # HTML 邮件内容
    html = f"""
    <html>
      <body>
        <h2>Service Desk 工单通知</h2>
        <p>尊敬的 {ticket['requester_name']}，</p>
        
        <p>您的工单状态已更新：</p>
        
        <table border="1" cellpadding="10">
          <tr><td><b>追踪码</b></td><td>{ticket['tracking_code']}</td></tr>
          <tr><td><b>标题</b></td><td>{ticket['title']}</td></tr>
          <tr><td><b>状态</b></td><td>{ticket['status']}</td></tr>
          <tr><td><b>更新时间</b></td><td>{ticket['updated_at']}</td></tr>
        </table>
        
        <p>
          <a href="http://your-server:8000/static/service_desk_track.html?code={ticket['tracking_code']}">
            点击查看工单详情
          </a>
        </p>
        
        <p>如有疑问，请回复此邮件。</p>
        
        <p>---<br>Service Desk 自动通知</p>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html, "html"))
    
    # 发送邮件
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
```

**通知时机**:

1. ✅ 工单创建时 - 发送确认邮件（含追踪码）
1. ✅ 状态变更时 - 发送状态更新通知
1. ✅ 工单完成时 - 发送完成通知
1. ✅ 收到评论时 - 发送评论通知

______________________________________________________________________

### 方式 3: 简单登录（可选）

**实现方案**: 基于邮箱的简单登录

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

security = HTTPBearer()

def generate_token(email: str) -> str:
    """生成访问令牌"""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, "secret_key", algorithm="HS256")

@app.post("/service-desk/login")
async def login_with_email(email: str):
    """邮箱登录（发送验证码）"""
    # 生成 6 位验证码
    code = random.randint(100000, 999999)
    
    # 发送验证码邮件
    send_verification_code(email, code)
    
    # 临时存储验证码（5分钟有效）
    VERIFICATION_CODES[email] = {
        "code": code,
        "expires_at": datetime.now() + timedelta(minutes=5)
    }
    
    return {"message": "验证码已发送到您的邮箱"}

@app.post("/service-desk/verify")
async def verify_code(email: str, code: int):
    """验证码验证"""
    stored = VERIFICATION_CODES.get(email)
    
    if not stored or stored["code"] != code:
        raise HTTPException(status_code=400, detail="验证码错误")
    
    if datetime.now() > stored["expires_at"]:
        raise HTTPException(status_code=400, detail="验证码已过期")
    
    # 生成访问令牌
    token = generate_token(email)
    
    return {"token": token, "email": email}

@app.get("/service-desk/my-tickets")
async def get_my_tickets(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取我的工单列表（需要登录）"""
    # 验证令牌
    payload = jwt.decode(credentials.credentials, "secret_key", algorithms=["HS256"])
    email = payload["email"]
    
    # 返回该邮箱的所有工单
    tickets = [t for t in SERVICE_DESK_TICKETS.values() if t["requester_email"] == email]
    return tickets
```

**优点**:

- 🔐 简单的身份验证
- 📋 可以查看"我的工单"
- 🔒 一定程度的安全性

**缺点**:

- 📧 需要邮件服务器
- 🔑 需要管理令牌
- 🛠️ 增加系统复杂度

______________________________________________________________________

## 📊 方案对比

| 方案 | 实现难度 | 用户体验 | 安全性 | 推荐度 |
|------|---------|---------|--------|--------|
| **Web 界面（当前）** | ⭐ 简单 | ⭐⭐⭐⭐ 很好 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ |
| **邮件通知** | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 极好 | ⭐⭐⭐⭐ 好 | ⭐⭐⭐⭐⭐ |
| **邮件创建工单** | ⭐⭐⭐ 复杂 | ⭐⭐⭐ 好 | ⭐⭐⭐ 中等 | ⭐⭐⭐ |
| **简单登录** | ⭐⭐ 中等 | ⭐⭐⭐ 好 | ⭐⭐⭐⭐ 好 | ⭐⭐⭐⭐ |

______________________________________________________________________

## 💡 推荐实施方案

### 阶段 1: 当前方案（已完成）✅

- Web 界面无需登录
- 通过追踪码查询工单

### 阶段 2: 邮件通知（强烈推荐）⭐⭐⭐⭐⭐

**优先级**: 高\
**工作量**: ~2-3 小时\
**价值**: 极大提升用户体验

**实现内容**:

1. 工单创建时发送确认邮件（含追踪码）
1. 状态变更时发送通知邮件
1. 工单完成时发送完成通知
1. 邮件中包含查询链接

### 阶段 3: 邮件创建工单（可选）

**优先级**: 中\
**工作量**: ~4-6 小时\
**价值**: 提供额外的提交渠道

### 阶段 4: 简单登录（可选）

**优先级**: 低\
**工作量**: ~3-4 小时\
**价值**: 方便查看"我的工单"

______________________________________________________________________

## 🚀 快速实施邮件通知

如果您希望立即实施邮件通知功能，我可以为您：

1. ✅ 添加 SMTP 配置到 `config.ini`
1. ✅ 实现邮件发送工具函数
1. ✅ 在工单创建/更新时自动发送邮件
1. ✅ 提供 HTML 邮件模板
1. ✅ 测试邮件发送功能

**需要的信息**:

- SMTP 服务器地址（如：smtp.gmail.com）
- SMTP 端口（如：587）
- 发件邮箱账号
- 发件邮箱密码/应用专用密码

______________________________________________________________________

## 📝 当前使用方式总结

### 业务方如何使用 Service Desk

**步骤 1: 访问 Service Desk**

```
打开浏览器 → 访问 http://your-server:8000/static/service_desk.html
```

**步骤 2: 提交工单**

```
选择"提交 Bug"或"提交需求" → 填写表单 → 提交
```

**步骤 3: 获取追踪码**

```
提交成功后显示追踪码（如：BUG-20251227-001）
```

**步骤 4: 查询工单**

```
访问追踪页面 → 输入追踪码 → 查看状态
或
直接访问: http://your-server:8000/static/service_desk_track.html?code=BUG-20251227-001
```

**无需**:

- ❌ 注册账号
- ❌ 登录系统
- ❌ 记住密码
- ❌ 安装软件

**只需**:

- ✅ 浏览器
- ✅ 网络连接
- ✅ 记住追踪码（或收藏查询链接）

______________________________________________________________________

## ❓ 您的选择

请告诉我您希望如何处理：

**选项 1**: 保持当前方案（Web 界面，无需登录）\
**选项 2**: 添加邮件通知功能（推荐）⭐⭐⭐⭐⭐\
**选项 3**: 实现完整的邮件集成（接收邮件创建工单）\
**选项 4**: 添加简单登录功能\
**选项 5**: 组合方案（如：Web + 邮件通知）

我可以立即为您实施任何选项！🚀

______________________________________________________________________

**文档版本**: v1.0\
**创建时间**: 2025-12-27
