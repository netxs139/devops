# 开源组件安全与许可证合规性扫描 (Security & License Scanning)

本文档详述了如何通过集成 **OWASP Dependency-Check** 实现对研发项目的开源依赖漏洞扫描及许可证合规性治理。

---

## 1. 数据模型与视图设计

### 1.1 核心数据表
系统通过 4 个核心表追踪扫描生命周期与风险数据：
- **`dependency_scans`**: 存储每次扫描的元数据（状态、时间、汇总统计）。
- **`dependencies`**: 存储项目依赖清单及对应的许可证信息。
- **`dependency_cves`**: 存储具体的 CVE 漏洞详情、严重性与修复建议。
- **`license_risk_rules`**: 预置许可证风险规则，定义各许可证的合规风险等级。

### 1.2 合规性分析视图
系统提供 `view_compliance_oss_license_risk_enhanced` 增强视图，用于 PMO 和安全部门进行全局风险透视。

---

## 2. 实施与部署指南

### 2.1 数据库迁移
执行 `devops_collector/plugins/dependency_check/add_dependency_check_tables.sql` 以创建表结构及预置 16+ 常见许可证规则（如 GPL, MIT, Apache 等）。

### 2.2 安装 Dependency-Check CLI
1. 下载最新版本：[GitHub Releases](https://github.com/jeremylong/DependencyCheck/releases)。
2. 解压并确保执行权限。
3. 测试版本：`./dependency-check.sh --version`。

### 2.3 配置 `config.ini`
在配置文件中添加 `[dependency_check]` 段：
```ini
[dependency_check]
cli_path = /path/to/dependency-check.sh
timeout = 600
report_dir = /var/lib/devops/dependency-reports  # 持久化存储路径
keep_reports = true                             # 是否保留原始 JSON 报告
report_retention_days = 90                       # 保留天数
auto_scan_enabled = false
scan_frequency_days = 7
```

---

## 3. 使用场景与操作示例

### 3.1 运行扫描任务
通过 `DependencyCheckWorker` 执行扫描：
```python
from devops_collector.plugins.dependency_check import DependencyCheckWorker

worker = DependencyCheckWorker(config)
scan_id = worker.run_scan(
    project_id=123,
    project_path='/path/to/project',
    project_name='my-app'
)
```

### 3.2 历史报告导入
支持从外部 CI/CD 环境导入已有的 JSON 报告进行持久化与入库分析：
```python
worker.import_existing_report(
    project_id=123,
    report_path='/path/to/existing/report.json'
)
```

### 3.3 审计与清理
- **许可证审计**: 通过 SQL 查询 `critical` 风险等级的依赖。
- **自动化清理**: 运行 `worker.cleanup_old_reports()` 以释放存储空间。

---

## 4. 许可证风险规则参考 (License Risk Rules)

| 许可证 | 风险等级 | 传染性 | 描述 |
| :--- | :--- | :--- | :--- |
| **GPL-3.0 / AGPL-3.0** | Critical | 是 | 强传染性，商业使用需高度警惕 |
| **LGPL-3.0 / MPL-2.0** | High/Medium | 是 | 弱/文件级传染性 |
| **Apache-2.0 / MIT** | Low | 否 | 商业友好，建议首选 |

---

## 5. 核心优势
- ✅ **全包管理器支持**: 涵盖 Maven, NPM, PyPI, NuGet, Go 等。
- ✅ **SPDX 标准化**: 自动对齐国际标准许可证 ID。
- ✅ **漏洞关联**: 自动关联 NVD 数据库中的 CVE 漏洞。
- ✅ **资产持久化**: 独立的报告存储体系，满足审计追溯需求。
