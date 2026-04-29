# 全局文档地图 (DOC_INDEX.md)

> **定位声明**：本项目所有文档资产（.md, .txt, .log）的“导航中枢”，遵循 Map & Reduce 策略，为 AI 审计与人工查阅提供单点索引。
> **维护方式**：由 `/doc-audit` 工作流强制同步更新。

---

## 🛠️ P0 级：核心调度与状态 (Root Meta-Docs)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `AGENTS.md` | **AI 调度中心**：定义指令映射、物理红线与协作原则。 |
| `contexts.md` | **技术宪章**：固化架构标准、编码原则、DB 协议与集成规范。 |
| `progress.txt` | **当前看板**：记录实时重点、下一步计划与最近完成项。 |
| `CHANGELOG.md` | **变更日志**：记录系统的版本演进与重大更新。 |
| `README.md` | **项目总纲**：环境搭建、uv 架构说明与快速启动指南。 |
| `CONTRIBUTING.md` | **贡献指南**：代码风格、分支策略与 PR 提交规范。 |
| `LICENSE` | **开源协议**：项目采用 Apache 2.0 协议进行授权与分发。 |

## 🤖 AI 逻辑：工作流与专家技能 (.agent/)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `.agent/workflows/` | **标准作业程序 (SOP)**：包含 `/task-kickoff`, `/doc-audit` 等原子指令流程。 |
| `.agent/skills/` | **专家大脑**：包含 `dbt-pipeline-auditor`, `mdm-integrity-arbiter` 等自动化审计能力。 |

## 📐 架构设计与模型 (Architecture & Design)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `docs/architecture/SYSTEM_DESIGN.md` | **核心设计**：涵盖 MDS 架构、数据分层、SDA 逻辑及演进路线。 |
| `docs/architecture/adr/` | **决策记录**：归档所有关键的技术架构决策 (ADRs)。 |
| `docs/api/DATA_DICTIONARY.md` | **数据字典**：详述数据库表结构、字段定义与业务语义。 |
| `docs/architecture-alignment.md`| **架构对齐清单**：用于验证实现与设计是否背离的核查表。 |

## 🚀 业务特性详解 (Feature Details)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `docs/features/COLLECTOR_PLUGINS.md` | **采集插件**：详述 GitLab, Sonar, Jenkins, Jira 等数据源集成细节。 |
| `docs/features/PLATFORM_FEATURES.md` | **平台功能**：详述 RBAC 2.0, GTM 测试管理, AI 辅助等核心模块。 |

## 📊 度量与分析计划 (Analytics & Metrics)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `docs/analytics/METRICS_GLOSSARY.md` | **指标词典**：统一定义 DORA, ROI, 流动效能等核心口径。 |
| `docs/analytics/plans/` | **分析方案**：针对 PMO, HR, Team 等不同维度的深度分析计划。 |

## 📖 指南与手册 (Guides & Manuals)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `docs/guides/DEPLOYMENT.md` | **部署手册**：涵盖 Docker 快速启动与手动安装、配置运维。 |
| `docs/guides/USER_GUIDE.md` | **用户手册**：面向开发与管理者的指标查阅及 DataHub 使用指南。 |
| `docs/guides/SECURITY_SCAN.md` | **安全审计**：详述 OWASP Dependency-Check 的集成与合规治理。 |
| `docs/guides/knowledge_harvest_protocol.md` | **知识收割协议**：定义如何提炼并记录知识。 |

## 📓 历史演进与归档 (History & Logs)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `docs/history/lessons-learned.log` | **避坑指南**：倒序记录踩坑经验、根因分析与规则固化。 |
| `docs/history/session-history.log` | **审计轨迹**：记录每次会话的关键决策、物理证据与交接状态。 |
| `docs/history/progress_archive.md` | **任务归档**：存放已从 progress.txt 迁出的陈旧任务记录。 |
| `docs/history/dev_logs/` | **开发日志**：记录 netxs.md 等个人开发心路历程与日结总结。 |

## 🧪 技术探针 (Spikes & Research)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `docs/spikes/` | **实验报告**：针对未知领域（如性能优化、WeCom 集成）的调研结论。 |

## ✅ 验证、审计与资产 (Verification & Assets)
| 文件路径 | 核心定位与作用域 |
| :--- | :--- |
| `docs/verification/` | **验收报告**：项目阶段性交付的测试报告与验收记录。 |
| `docs/assets/sample_data/` | **示例数据**：归档项目所需的 .csv 静态数据资产。 |
