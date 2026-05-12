# --- 阶段 1: 构建环境 (Builder) ---
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# 安装编译时依赖
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 UV (改用 pip 安装以避开镜像拉取限制)
RUN pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

# 预安装 Python 依赖 (利用缓存层)
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --index-url ${PIP_INDEX_URL}

# 拷贝项目源码并执行安装 (非开发模式)
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- 阶段 2: 运行环境 (Final) ---
FROM python:3.11-slim-bookworm

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
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动脚本处理
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "devops_portal.main:app", "--host", "0.0.0.0", "--port", "8000"]

