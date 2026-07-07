# --- 阶段 1: 构建环境 (Builder) ---
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/venv

# 安装编译时依赖
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 UV (改用 pip 安装以避开镜像拉取限制)
RUN pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝依赖的外部组件 (以供 uv sync 解析路径依赖)
COPY amdp/identity_module /amdp/identity_module
COPY amdp/notification-kit /amdp/notification-kit

# 预安装 Python 依赖 (利用缓存层)
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG INSTALL_DEV=true
COPY devops/pyproject.toml devops/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_DEV" = "true" ]; then \
        uv sync --frozen --no-install-project --all-extras --index-url ${PIP_INDEX_URL}; \
    else \
        uv sync --frozen --no-install-project --no-dev --index-url ${PIP_INDEX_URL}; \
    fi

# 拷贝项目源码并执行安装 (非开发模式)
COPY devops/ .
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_DEV" = "true" ]; then \
        uv sync --frozen --all-extras; \
    else \
        uv sync --frozen --no-dev; \
    fi



# --- 阶段 2: 运行环境 (Final) ---
FROM python:3.12-slim-bookworm

WORKDIR /app

# 仅安装运行时必要的库
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装运行时 UV
RUN pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

# 从 Builder 阶段拷贝虚拟环境和代码
COPY --from=builder /venv /venv
COPY --from=builder /app /app
COPY --from=builder /amdp /amdp

# 设置环境变量
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV=/venv
ENV UV_PROJECT_ENVIRONMENT=/venv
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动脚本处理
COPY devops/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "devops_portal.main:app", "--host", "0.0.0.0", "--port", "8000"]
