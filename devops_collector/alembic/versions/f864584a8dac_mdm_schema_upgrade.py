"""mdm_schema_upgrade

Revision ID: f864584a8dac
Revises: a1b2c3d4e5f7
Create Date: 2026-07-07 14:36:44.628229

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f864584a8dac"  # pragma: allowlist secret
down_revision: str | None = "a1b2c3d4e5f7"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    from sqlalchemy import inspect

    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. 容错创建 mdm_customers
    if "mdm_customers" not in existing_tables:
        op.create_table(
            "mdm_customers",
            sa.Column("tenant_id", sa.String(length=32), server_default="default", nullable=False, comment="租户ID"),
            sa.Column("customer_id", sa.UUID(), nullable=False, comment="客户唯一标识"),
            sa.Column("customer_code", sa.String(length=100), nullable=False, comment="客户业务唯一编码"),
            sa.Column("customer_name", sa.String(length=255), nullable=False, comment="客户公司名称"),
            sa.Column("usci", sa.String(length=18), nullable=True, comment="统一社会信用代码"),
            sa.Column("industry_category", sa.String(length=100), nullable=True, comment="行业分类"),
            sa.Column("customer_tier", sa.String(length=50), nullable=True, comment="客户级别"),
            sa.Column("business_owner_id", sa.String(length=32), nullable=True, comment="商务负责人"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("sync_version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("effective_from", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_current", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
            sa.PrimaryKeyConstraint("customer_id"),
            comment="客户主数据表",
        )
        op.create_index("idx_mdm_customer_active_lookup", "mdm_customers", ["customer_code"], unique=False, postgresql_where="is_current IS TRUE")
        op.create_index("uq_mdm_customer_code_active", "mdm_customers", ["customer_code"], unique=True, postgresql_where="is_current IS TRUE")
        op.create_index("uq_mdm_customer_usci_active", "mdm_customers", ["usci"], unique=True, postgresql_where="is_current IS TRUE AND usci IS NOT NULL")

    # 2. 检查并升级 mdm_projects.id, mdm_products.id, mdm_vendors.id 为 UUID (仅当它们在生产库中仍为 VARCHAR 类型时)
    # 开发环境由于已重置，列已经是 UUID，无需做 alter
    for table_name, pk_col in [("mdm_projects", "id"), ("mdm_products", "id"), ("mdm_vendors", "id")]:
        if table_name in existing_tables:
            columns = inspector.get_columns(table_name)
            for col in columns:
                if col["name"] == pk_col and not isinstance(col["type"], sa.UUID):
                    # 生产环境转换 SQL
                    op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {pk_col} TYPE UUID USING {pk_col}::uuid")

    # 3. 升级关系表中的字段类型 (仅当旧数据库中它们是 VARCHAR 时)
    # sd_customer_identities.customer_company_id
    if "sd_customer_identities" in existing_tables:
        cols = inspector.get_columns("sd_customer_identities")
        for col in cols:
            if col["name"] == "customer_company_id" and not isinstance(col["type"], sa.UUID):
                op.execute("ALTER TABLE sd_customer_identities ALTER COLUMN customer_company_id TYPE UUID USING customer_company_id::uuid")
                # 重新添加外键约束
                op.create_foreign_key(
                    "fk_customer_identity_company",
                    "sd_customer_identities",
                    "mdm_customers",
                    ["customer_company_id"],
                    ["customer_id"],
                )

    # agile_product_mappings.product_id
    if "agile_product_mappings" in existing_tables:
        cols = inspector.get_columns("agile_product_mappings")
        for col in cols:
            if col["name"] == "product_id" and not isinstance(col["type"], sa.UUID):
                op.execute("ALTER TABLE agile_product_mappings ALTER COLUMN product_id TYPE UUID USING product_id::uuid")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("mdm_customers")
