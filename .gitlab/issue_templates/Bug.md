<!-- 
⚠️ 重要提示：请务必完成以下必填项，否则 Bug 可能无法被正确处理！

必填标签（请在下方选择）：
✅ 严重程度 (Severity): S1/S2/S3/S4
✅ 优先级 (Priority): P0/P1/P2/P3
✅ Bug 类别 (Bug Category): 9 种分类中选择 1 种

标题格式要求：[P?][S?][类别] 简短描述
示例：[P0][S1][代码错误] 空指针异常导致服务崩溃
-->

# 🐛 Bug 报告

> **📋 填写指南**:
>
> - 请详细描述 Bug 现象和复现步骤
> - **必须选择**下方的严重程度、优先级、Bug 类别及**发现省份**标签
> - 标题中请包含优先级、严重程度和类别信息
> - 不完整的 Bug 报告可能会被要求补充信息

______________________________________________________________________

## Bug 描述

[清晰描述 Bug 的现象]

## 复现步骤

1. 步骤 1
1. 步骤 2
1. 步骤 3

## 预期行为 vs 实际行为

- **预期**: [描述预期的正确行为]
- **实际**: [描述实际发生的错误行为]

## 环境信息

- 操作系统: [例如: Windows 10 / Ubuntu 20.04]
- 浏览器: [例如: Chrome 120 / Firefox 115]
- 版本: [例如: v1.2.3]
- 环境: [例如: 生产环境 / 测试环境]

## 🏷️ Bug 分类（⚠️ 必填项）

> **❗ 重要**: 以下四个维度的标签都是**必选项**，请务必勾选！

### ⭐ 严重程度 (Severity) - 必选

请根据以下标准选择严重程度标签:

- [ ] `severity::S1` - 致命: 系统崩溃、数据丢失、安全漏洞
- [ ] `severity::S2` - 严重: 核心功能不可用，无替代方案
- [ ] `severity::S3` - 一般: 功能异常，有替代方案
- [ ] `severity::S4` - 轻微: UI 问题、文案错误

### ⭐ 优先级 (Priority) - 选选

请根据业务影响选择优先级标签:

- [ ] `priority::P0` - 紧急: 立即处理 (4小时内)
- [ ] `priority::P1` - 高: 1-2天内处理
- [ ] `priority::P2` - 中: 1周内处理
- [ ] `priority::P3` - 低: 下个迭代处理

### ⭐ Bug 类别 (Bug Category) - 必选

请根据问题根因选择 Bug 类别:

- [ ] `bug-category::test-script` - 测试脚本: 自动化测试脚本错误、测试用例设计问题
- [ ] `bug-category::code-error` - 代码错误: 逻辑错误、空指针、数组越界等编码问题
- [ ] `bug-category::configuration` - 配置相关: 配置文件错误、环境变量问题、参数配置不当
- [ ] `bug-category::design-defect` - 设计缺陷: 架构设计问题、接口设计不合理、业务逻辑缺陷
- [ ] `bug-category::deployment` - 安装部署: 部署脚本错误、依赖缺失、环境兼容性问题
- [ ] `bug-category::performance` - 性能问题: 响应慢、内存泄漏、CPU 占用高、并发问题
- [ ] `bug-category::security` - 安全相关: SQL 注入、XSS、权限漏洞、数据泄露
- [ ] `bug-category::standard` - 标准规范: 代码规范违反、文档不符合标准、命名不规范
- [ ] `bug-category::other` - 其他: 无法归类的其他问题

### ⭐ Bug 来源 (Bug Source) - 必选

**用于统计缺陷逃逸率**

- [ ] `bug-source::production` - **生产环境发现**: 在生产环境中发现的 Bug（缺陷逃逸）
- [ ] `bug-source::non-production` - **非生产环境发现**: 在开发、测试、预发布等环境发现的 Bug

> **💡 说明**:
>
> - **生产环境**: 正式对外提供服务的环境
> - **非生产环境**: 开发环境、测试环境、UAT 环境、预发布环境等
> - **缺陷逃逸率** = 生产环境发现的 Bug / 总 Bug 数 × 100%

### ⭐ Bug 发现省份 (Province) - 必选

**用于按地域统计 Bug 分布**

**直辖市**:

- [ ] `province::beijing` - 北京
- [ ] `province::shanghai` - 上海
- [ ] `province::tianjin` - 天津
- [ ] `province::chongqing` - 重庆

**省份**:

- [ ] `province::anhui` - 安徽
- [ ] `province::fujian` - 福建
- [ ] `province::gansu` - 甘肃
- [ ] `province::guangdong` - 广东
- [ ] `province::guizhou` - 贵州
- [ ] `province::hainan` - 海南
- [ ] `province::hebei` - 河北
- [ ] `province::henan` - 河南
- [ ] `province::heilongjiang` - 黑龙江
- [ ] `province::hubei` - 湖北
- [ ] `province::hunan` - 湖南
- [ ] `province::jilin` - 吉林
- [ ] `province::jiangsu` - 江苏
- [ ] `province::jiangxi` - 江西
- [ ] `province::liaoning` - 辽宁
- [ ] `province::qinghai` - 青海
- [ ] `province::shaanxi` - 陕西
- [ ] `province::shandong` - 山东
- [ ] `province::shanxi` - 山西
- [ ] `province::sichuan` - 四川
- [ ] `province::yunnan` - 云南
- [ ] `province::zhejiang` - 浙江

**自治区**:

- [ ] `province::guangxi` - 广西
- [ ] `province::neimenggu` - 内蒙古
- [ ] `province::ningxia` - 宁夏
- [ ] `province::xinjiang` - 新疆
- [ ] `province::xizang` - 西藏

**其他**:

- [ ] `province::nationwide` - **全国** - 全国性问题或无法确定具体省份

> **💡 说明**:
>
> - 选择 Bug 最初发现或报告的省份
> - 如果是全国性问题或无法确定具体省份，请选择"全国"
> - 此标签用于按地域分析 Bug 分布和趋势

## 📎 附件

**请上传相关附件以帮助快速定位问题**:

### 推荐上传的附件类型

- **截图**: Bug 现象的屏幕截图（PNG, JPG）
- **日志文件**: 错误日志、系统日志（LOG, TXT）
- **错误堆栈**: 完整的错误堆栈信息
- **录屏**: Bug 复现过程的视频（MP4, GIF）
- **配置文件**: 相关的配置文件（如有必要）
- **测试数据**: 用于复现的测试数据（ZIP, JSON, CSV）

### 上传方式

1. **拖拽上传**: 直接将文件拖拽到此处
1. **点击上传**: 点击下方的 📎 "Attach a file" 按钮
1. **粘贴上传**: 截图后直接 Ctrl+V 粘贴（仅图片）

> **💡 提示**:
>
> - 单个文件大小限制: 通常为 10MB（具体限制请咨询管理员）
> - 支持的文件格式: 图片、文档、压缩包、日志文件等
> - 敏感信息请打码处理

**附件列表**:

<!-- 在此处上传附件，GitLab 会自动生成链接 -->

## 根因分析（可选）

[如果已知，请描述问题的根本原因]

## 解决方案（可选）

[如果有建议的解决方案，请描述]

______________________________________________________________________

## ✅ 提交前检查清单

在提交此 Bug 报告前，请确认：

- [ ] ✅ 已选择**严重程度** (severity::S?)
- [ ] ✅ 已选择**Bug 类别** (bug-category::?)
- [ ] ✅ 已选择**Bug 来源** (bug-source::production/non-production)
- [ ] ✅ 已选择**发现省份** (province::?)
- [ ] ✅ 标题格式正确: `[S?][类别] 简短描述`
- [ ] ✅ 已添加 `type::bug` 标签
- [ ] ✅ 复现步骤清晰完整
- [ ] ✅ 已附加相关截图或日志（如有）

______________________________________________________________________

**标签建议**: `type::bug`, `severity::S?`, `bug-category::?`, `bug-source::?`, `province::?`

**标题示例**:

- `[P0][S1][代码错误] 空指针异常导致服务崩溃`
- `[P1][S2][性能] 查询响应时间超过 5 秒`
- `[P2][S3][配置] 数据库连接池配置不当`

______________________________________________________________________

> **💡 提示**: 标签不完整的 Bug 报告可能会被自动标记为 `needs-labels`，并要求补充信息。

______________________________________________________________________

## 🚪 关闭说明 (Closing Instructions)

> **操作指引**: 关闭议题前，请在下方选择关闭原因（通过评论区执行指令，GitLab 会自动打标并关闭议题）。

- **已完成**: `/label ~"resolution::done" /close`
- **重复**: `/label ~"resolution::duplicate" /close`
- **延期**: `/label ~"resolution::postponed" /close`
- **不做**: `/label ~"resolution::wontfix" /close`
- **设计如此**: `/label ~"resolution::by_design" /close`
- **无法重现**: `/label ~"resolution::cannot_reproduce" /close`
- **转为需求**: `/label ~"resolution::as_requirement" /close`

______________________________________________________________________

/label ~"type::bug" ~"status::draft"
/milestone %"Current_Milestone"
