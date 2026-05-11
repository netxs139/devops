# DevOps Platform 自动化运维与任务管理 (Justfile)
# -----------------------------------------------------------
#  标准化本地开发、容器构建与 CI/CD 流程
#  所有容器操作均默认在 api 容器内执行，确保环境一致性
# -----------------------------------------------------------

set dotenv-load := true
set shell := ["bash", "-c"]

# 统一变量定义 (优先从 .env 读取)
NEXUS_PYPI_URL        := env_var_or_default("NEXUS_PYPI_URL", "http://192.168.5.64:8081/repository/group-pypi/simple")
NEXUS_DOCKER_REGISTRY := env_var_or_default("NEXUS_DOCKER_REGISTRY", "192.168.5.64:8082")


# 动态环境判定 (SSOT: 环境变量优先)
COMPOSE_FILE        := if env_var_or_default("PROD", "false") == "true" { "docker-compose.prod.yml" } else { "docker-compose.yml" }
COMPOSE_CMD         := "docker-compose -f " + COMPOSE_FILE
EXEC_CMD            := COMPOSE_CMD + " exec -T api uv run"
SHELL_EXEC          := COMPOSE_CMD + " exec -T api"

# =============================================================================
# 顶级入口 (Unified Entry Points) - 确立单一入口绝对权威
# =============================================================================

# 显示所有可用指令
default:
    @just --list

# [极速开发] 一键进入战斗状态：清理 -> 启动 -> 诊断 -> 实时日志
dev: clean
    @echo "🚀 Launching Development Environment..."
    just up
    just diagnose
    just logs

# [标准启动] 启动服务并执行增量数据对齐
start: up
    @echo "✅ System started. Running baseline data alignment..."
    {{EXEC_CMD}} python scripts/cli.py init --all

# [全量部署] 生产级一键部署：门禁校验 -> 构建 -> 启动 -> 初始化
deploy: verify build up init docs
    @echo "🌐 DevOps Platform deployed successfully!"

# =============================================================================
# 核心生命周期 (Core Lifecycle)
# =============================================================================

# 启动容器并等待健康检查
up:
    @echo "Starting services (Env: {{COMPOSE_FILE}})..."
    {{COMPOSE_CMD}} up -d --wait

# 停止并移除容器 (保持幂等)
down:
    @echo "Stopping services..."
    {{COMPOSE_CMD}} down --remove-orphans

# 物理重启
restart: down up

# 构建镜像 (强制/可选 门禁校验)
# 用法: just build (带质检) | just build --fast (跳过质检)
build mode="full":
    @if [ "{{mode}}" != "fast" ]; then \
        echo "🛡️ Running Pre-build Quality Gate..."; \
        just lint; \
    fi
    @echo "🏗️ Building Docker images..."
    {{COMPOSE_CMD}} build --build-arg PIP_INDEX_URL={{NEXUS_PYPI_URL}}

# 进入 API 容器终端
shell:
    {{COMPOSE_CMD}} exec api /bin/bash

# 查看实时日志
logs:
    {{COMPOSE_CMD}} logs -f --tail=100

# [初始化] 使用统一命令总线进行数据初始化 (支持事务回滚)
init:
    @echo "Initializing data through Command Bus..."
    just install
    {{EXEC_CMD}} python scripts/cli.py init --all

# 使用 uv sync 同步依赖 (含内网 Nexus 重试逻辑)
install:
    @echo "Tiered Sync (Nexus Primary x3 -> Tsinghua Fallback)..."
    uv run scripts/cli.py run --module sync_deps --frozen

# [本地] 初始化宿主机开发环境
init-dev:
    @echo "Local Dev Init (Nexus Primary x3 -> Tsinghua Fallback)..."
    uv run scripts/cli.py run --module sync_deps --dev


# =============================================================================
# 验证与测试 (Verification & Testing)
# =============================================================================

# [MANDATORY] 全量校验：Lint -> TypeCheck -> Imports -> Docs -> SAST -> Test + Cov
verify: lint typecheck check-imports docs-verify scan-sast
    @echo "Running tests with coverage audit (Target: 80%)..."
    {{EXEC_CMD}} pytest tests/unit/ tests/integration/ --cov=devops_collector --cov=devops_portal --cov-report=term-missing --cov-fail-under=70

# 代码质量检查 (Ruff)
lint:
    @echo "Running Ruff check..."
    uv run ruff check devops_collector/ devops_portal/ tests/ scripts/

# 代码格式化
fmt:
    @echo "Formatting code with Ruff..."
    uv run ruff format devops_collector/ devops_portal/ tests/ scripts/
    uv run ruff check --select I --fix devops_collector/ devops_portal/ tests/ scripts/

# 自动修复 Ruff 发现的逻辑问题
ruff-fix:
    uv run ruff check --fix devops_collector/ devops_portal/ tests/ scripts/

# 静态类型检查 (MyPy)
typecheck:
    @echo "Running MyPy type checking..."
    uv run mypy devops_collector/ devops_portal/

# 检查核心模块导入依赖
check-imports:
    @echo "Checking module imports..."
    {{EXEC_CMD}} python scripts/cli.py check --module imports

# [MANDATORY] 架构合规性审计 (Anti-Patterns Check)
arch-audit:
    @echo "Running Architecture & Anti-Pattern Audit..."
    uv run python scripts/arch_auditor.py

# 数据字典一致性校验
docs-verify:
    @echo "Verifying Data Dictionary freshness..."
    {{EXEC_CMD}} python scripts/check_data_dict_freshness.py

# [MANDATORY] 核心卡点：代码合并前全量校验 (Lint -> Test -> Build)
full-gate:
    @echo "Launching Project Full Gate (Grader 3)..."
    uv run python scripts/gatekeeper.py --mode full

# [L2/CI] 快速卡点：跳过容器构建阶段
fast-gate:
    uv run python scripts/gatekeeper.py --mode fast

# 运行单元测试
test:
    {{EXEC_CMD}} pytest tests/unit/ -v

# 运行集成测试
test-int:
    {{EXEC_CMD}} pytest tests/integration/ -v

# =============================================================================
# 系统诊断与数据操作 (Ops & Data)
# =============================================================================

# 系统综合诊断
diagnose:
    {{EXEC_CMD}} python scripts/cli.py diag --all

# 数据库专项诊断
diag-db:
    {{EXEC_CMD}} python scripts/cli.py diag --module db

# 消息队列专项诊断
diag-mq:
    {{EXEC_CMD}} python scripts/diag_mq.py

# [性能诊断] 数据库执行计划分析 (EXPLAIN ANALYZE)
profile-db args="":
    @echo "Running EXPLAIN ANALYZE profiling..."
    {{EXEC_CMD}} python scripts/profile_db.py {{args}}

# [性能诊断] Python 运行时采样 (py-spy)
profile-code args="":
    @echo "Running py-spy profiling..."
    {{EXEC_CMD}} py-spy record -o profile.svg -- python {{args}}

# 手动触发全量数据同步
sync-all:
    @echo "Triggering full sync..."
    {{EXEC_CMD}} python -m devops_collector.scheduler --force-all --once
    {{EXEC_CMD}} python -m devops_collector.worker --once

# 执行 dbt 建模转换
dbt-build:
    @echo "Running dbt transformations..."
    {{SHELL_EXEC}} bash -c "cd dbt_project && dbt build"

# 同步元数据到 DataHub
datahub-ingest:
    @echo "Ingesting metadata to DataHub..."
    {{COMPOSE_CMD}} run --rm datahub-cli datahub ingest -c datahub/recipe_postgres.yml
    {{COMPOSE_CMD}} run --rm datahub-cli datahub ingest -c datahub/recipe_dbt.yml

# =============================================================================
# 安全审计 (Security Audit)
# =============================================================================

# 源码机密审计 (detect-secrets)
scan-secrets:
    @echo "Scanning for hardcoded secrets..."
    uv run detect-secrets scan --baseline .secrets.baseline --exclude-files ".*/tests/.*" --exclude-files ".*\.lock"

# 代码静态安全审计 (Bandit)
scan-sast:
    @echo "Running Bandit SAST..."
    {{EXEC_CMD}} bandit -r devops_collector/ devops_portal/ -ll -o reports/security/bandit_report.json

# 依赖漏洞审计 (Safety)
scan-deps:
    @echo "Checking dependency vulnerabilities..."
    {{EXEC_CMD}} safety check --ignore 64459 --ignore 64396 --ignore 86269 --ignore 89047 --json > reports/security/safety_report.json

# [SECURITY] 全量安全卡点
security-audit: scan-secrets scan-sast scan-deps

# =============================================================================
# 离线打包与生产部署 (Deployment & Packaging)
# =============================================================================

# 构建并打包镜像为 tar 文件
package: pull-images
    @echo "Packaging images to devops-platform.tar..."
    docker build -t devops-platform:latest .
    docker save -o devops-platform.tar devops-platform:latest

# 服务器专用：离线加载并部署 [Windows]
[windows]
deploy-offline:
    @if (Test-Path devops-platform.tar) { docker load -i devops-platform.tar }
    {{COMPOSE_CMD}} up -d --wait --no-build
    {{EXEC_CMD}} python -m devops_collector.utils.schema_sync
    just init-prod-data

# 服务器专用：离线加载并部署 [Linux]
[linux]
deploy-offline:
    @if [ -f devops-platform.tar ]; then echo "Loading image..."; docker load -i devops-platform.tar; fi
    {{COMPOSE_CMD}} up -d --wait --no-build
    {{EXEC_CMD}} python -m devops_collector.utils.schema_sync
    just init-prod-data

# 内部调用：生产环境数据初始化
init-prod-data:
    {{EXEC_CMD}} python scripts/cli.py init --module rbac
    {{EXEC_CMD}} python scripts/cli.py init --module organizations
    {{EXEC_CMD}} python scripts/cli.py run --module import_employees

# 生产环境一键部署 (联网模式)
deploy-prod:
    {{COMPOSE_CMD}} down --remove-orphans
    {{COMPOSE_CMD}} build
    {{COMPOSE_CMD}} up -d --wait
    just init-prod-data

# 查看生产日志
prod-logs:
    {{COMPOSE_CMD}} logs -f --tail=100

# =============================================================================
# E2E 测试 (Playwright)
# =============================================================================

# 安装 E2E 测试依赖
e2e-install:
    uv sync --extra e2e
    playwright install chromium

# 运行 E2E 测试 (无头模式)
e2e-test:
    pytest tests/e2e/ -v --headed=false

# 运行 E2E 测试并保留追踪
e2e-trace:
    pytest tests/e2e/ -v --tracing=retain-on-failure

# 查看 E2E 追踪结果
e2e-show-trace:
    playwright show-trace test-results/

# =============================================================================
# 环境卫生与工具 (Maintenance)
# =============================================================================

# 检查基础镜像并执行预拉取加速 (Nexus -> Official) [Windows]
[windows]
pull-images:
    powershell -Command " \
        $$images = @('python:3.11-slim-bookworm', 'postgres:15-alpine', 'rabbitmq:3-management-alpine', 'astral-sh/uv:latest'); \
        foreach ($$img in $$images) { \
            if (docker images -q $$img) { continue; } \
            $$nexusImg = '{{NEXUS_DOCKER_REGISTRY}}/' + $$img; \
            & docker pull $$nexusImg 2>&1 | Out-Null; \
            if ($$LASTEXITCODE -eq 0) { \
                docker tag $$nexusImg $$img; \
                docker rmi $$nexusImg; \
                continue; \
            } \
            docker pull $$img; \
        } \
    "

# 检查基础镜像并执行预拉取加速 (Nexus -> Official) [Linux]
[linux]
pull-images:
    bash -c " \
        for img in python:3.11-slim-bookworm postgres:15-alpine rabbitmq:3-management-alpine astral-sh/uv:latest; do \
            if docker images -q \"\$img\" | grep -q .; then continue; fi; \
            nexus_img='{{NEXUS_DOCKER_REGISTRY}}/\$img'; \
            if docker pull \"\$nexus_img\" 2>/dev/null; then \
                docker tag \"\$nexus_img\" \"\$img\"; \
                docker rmi \"\$nexus_img\"; \
            else \
                docker pull \"\$img\"; \
            fi; \
        done; \
    "

# [Windows] 清理临时文件
[windows]
clean:
    @echo "Cleaning temporary files (Windows)..."
    powershell -Command " \
        Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; \
        Get-ChildItem -Path . -Include *.pyc,*.pyo,.coverage,*.tmp -File -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue; \
        if (Test-Path .pytest_cache) { Remove-Item -Path .pytest_cache -Recurse -Force }; \
        if (Test-Path .ruff_cache) { Remove-Item -Path .ruff_cache -Recurse -Force }; \
        if (Test-Path .agent\scratch) { Get-ChildItem .agent\scratch | Remove-Item -Force }; \
    "

# [Linux] 清理临时文件
[linux]
clean:
    @echo "Cleaning temporary files (Linux)..."
    find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
    find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -not -path "./.venv/*" -delete
    rm -rf .coverage .pytest_cache .ruff_cache test-results
    @echo "Done."

# 自动生成/更新数据字典
docs:
    @echo "Generating Data Dictionary..."
    {{EXEC_CMD}} python scripts/generate_data_dictionary.py

# =============================================================================
# 进度管理 (Progress Management)
# =============================================================================

# 添加新任务到进度表
progress-add task:
    @uv run python scripts/progress_manager.py --add "{{task}}"

# 标记任务为已完成 (输入任务编号)
progress-done id:
    @uv run python scripts/progress_manager.py --done {{id}}

# 更新当前重点 (Focus)
progress-focus content:
    @uv run python scripts/progress_manager.py --update-focus "{{content}}"

# 镜像未选选项到任务列表 (用分号分隔多个任务)
progress-mirror tasks:
    @uv run python scripts/progress_manager.py --mirror-tasks "{{tasks}}"

# 归档超过 5 条的已完成任务
progress-archive:
    @uv run python scripts/progress_manager.py --archive
