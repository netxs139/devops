import csv
import logging
import uuid
from pathlib import Path

from passlib.context import CryptContext

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import (
    SysMenu,
    SysRole,
    SysRoleMenu,
    User,
    UserCredential,
    UserRole,
)


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 默认内置数据定义 (Built-in Defaults) ---
DEFAULT_ROLES = [
    {"id": 1, "name": "系统管理员", "key": "SYSTEM_ADMIN", "scope": 1},
    {"id": 2, "name": "管理层", "key": "EXECUTIVE_MANAGER", "scope": 2},
    {"id": 3, "name": "部门经理", "key": "DEPT_MANAGER", "scope": 3},
    {"id": 4, "name": "项目经理", "key": "PROJECT_MANAGER", "scope": 4},
    {"id": 5, "name": "普通员工", "key": "REGULAR_USER", "scope": 5},
]

DEFAULT_MENUS = [
    {"id": 1, "pid": 0, "name": "平台管理", "path": "/admin", "type": "M", "icon": "setting", "perm": "sys:admin:view"},
    {"id": 101, "pid": 1, "name": "组织架构", "path": "/admin/org", "type": "C", "icon": "tree", "perm": "sys:org:view"},
    {"id": 102, "pid": 1, "name": "用户管理", "path": "/admin/user", "type": "C", "icon": "user", "perm": "sys:user:view"},
    {"id": 103, "pid": 1, "name": "产品定义", "path": "/admin/product", "type": "C", "icon": "shopping-cart", "perm": "sys:product:view"},
    {"id": 104, "pid": 1, "name": "项目主表", "path": "/admin/project", "type": "C", "icon": "project", "perm": "sys:project:view"},
    {"id": 2, "pid": 0, "name": "研发协同", "path": "/devops", "type": "M", "icon": "rocket", "perm": "sys:devops:view"},
    {"id": 201, "pid": 2, "name": "需求池", "path": "/devops/backlog", "type": "C", "icon": "unordered-list", "perm": "pm:backlog:view"},
    {"id": 202, "pid": 2, "name": "迭代看板", "path": "/devops/iteration", "type": "C", "icon": "dashboard", "perm": "pm:iteration:view"},
    {"id": 203, "pid": 2, "name": "质量门禁", "path": "/devops/quality", "type": "C", "icon": "safety-certificate", "perm": "qa:gate:view"},
    {"id": 3, "pid": 0, "name": "测试管理", "path": "/test", "type": "M", "icon": "experiment", "perm": "sys:test:view"},
    {"id": 301, "pid": 3, "name": "测试用例", "path": "/test/cases", "type": "C", "icon": "container", "perm": "qa:test:view"},
    {"id": 302, "pid": 3, "name": "追溯矩阵", "path": "/test/rtm", "type": "C", "icon": "deployment-unit", "perm": "qa:rtm:view"},
    {"id": 4, "pid": 0, "name": "服务支持", "path": "/service", "type": "M", "icon": "customer-service", "perm": "sys:service:view"},
    {"id": 401, "pid": 4, "name": "反馈中心", "path": "/service/desk", "type": "C", "icon": "message", "perm": "sd:ticket:view"},
    {"id": 402, "pid": 4, "name": "知识库", "path": "/service/kb", "type": "C", "icon": "read", "perm": "sd:kb:view"},
    {"id": 5, "pid": 0, "name": "效能看板", "path": "/analytics", "type": "M", "icon": "line-chart", "perm": "sys:analytics:view"},
    {"id": 501, "pid": 5, "name": "DORA指标", "path": "/analytics/dora", "type": "C", "icon": "thunderbolt", "perm": "ana:dora:view"},
    {"id": 502, "pid": 5, "name": "成本分析", "path": "/analytics/cost", "type": "C", "icon": "account-book", "perm": "ana:cost:view"},
]


class Command(BaseCommand):
    help = "初始化 RBAC 权限系统脚本（内置默认值 + 业务自适应版）"

    def add_arguments(self, parser):
        parser.add_argument("--force-admin", action="store_true", help="强制更新 admin 用户的密码")

    def handle(self, *args, **options):
        try:
            # 1. 确保 admin 用户
            admin_email = "admin@tjhq.com"
            admin_user = self.session.query(User).filter_by(primary_email=admin_email, is_current=True).first()
            if not admin_user:
                uid = uuid.uuid4()
                admin_user = User(
                    global_user_id=uid,
                    username="admin",
                    full_name="系统管理员",
                    primary_email=admin_email,
                    is_active=True,
                    is_current=True,
                )
                self.session.add(admin_user)
                self.session.flush()
                self.session.add(UserCredential(user_id=uid, password_hash=pwd_context.hash("admin_password_123!")))
            elif options.get("force_admin"):
                cred = self.session.query(UserCredential).filter_by(user_id=admin_user.global_user_id).first()
                if cred:
                    cred.password_hash = pwd_context.hash("admin_password_123!")
                    self.stdout.write("Admin password reset successfully.")

            # 2. 加载基础数据
            self._load_menus()
            self._load_roles()

            # 3. 自动权限同步
            self._ensure_auto_permissions()

            # 4. 兜底绑定 admin 角色
            ar = self.session.query(SysRole).filter_by(role_key="SYSTEM_ADMIN").first()
            if ar and not self.session.query(UserRole).filter_by(user_id=admin_user.global_user_id, role_id=ar.id).first():
                self.session.add(UserRole(user_id=admin_user.global_user_id, role_id=ar.id))

            self.session.flush()
            self.stdout.write("🎉 RBAC 系统初始化/同步完成。\n")
            return True
        except Exception as e:
            logger.error(f"RBAC 初始化失败: {e}")
            return False

    def _ensure_auto_permissions(self):
        """【业务常识授权】超管拥有一切，业务经理拥有非敏感菜单。"""
        admin_role = self.session.query(SysRole).filter_by(role_key="SYSTEM_ADMIN").first()
        business_roles = self.session.query(SysRole).filter(SysRole.role_key.in_(["EXECUTIVE_MANAGER", "DEPT_MANAGER"])).all()

        if not admin_role:
            return

        all_menus = self.session.query(SysMenu).all()
        # 平台管理分支的 ID 集合 (ID 为 1 极其子孙)
        admin_branch_ids = {1}
        for m in all_menus:
            if m.parent_id == 1 or (100 <= m.id < 200):
                admin_branch_ids.add(m.id)

        existing = set(self.session.query(SysRoleMenu.role_id, SysRoleMenu.menu_id).all())
        to_add = []

        for menu in all_menus:
            if (admin_role.id, menu.id) not in existing:
                to_add.append(SysRoleMenu(role_id=admin_role.id, menu_id=menu.id))
                existing.add((admin_role.id, menu.id))

            if menu.id not in admin_branch_ids:
                for br in business_roles:
                    if (br.id, menu.id) not in existing:
                        to_add.append(SysRoleMenu(role_id=br.id, menu_id=menu.id))
                        existing.add((br.id, menu.id))

        if to_add:
            self.session.bulk_save_objects(to_add)
            self.stdout.write(f"已自动分配 {len(to_add)} 项系统权限关联。\n")

    def _load_menus(self):
        csv_path = Path("docs/assets/sample_data/sys_menus.csv")
        if csv_path.exists():
            self.stdout.write("从 CSV 加载菜单配置...\n")
            with open(csv_path, encoding="utf-8-sig") as f:
                data = list(csv.DictReader(f))
                for row in data:
                    mid = int(row["ID"])
                    pid = int(row["父ID"])
                    m = self.session.query(SysMenu).get(mid) or SysMenu(id=mid)
                    m.menu_name, m.parent_id = row["菜单名称"], (pid if pid != 0 else None)
                    m.path, m.menu_type, m.icon = row["路由路径"], row["菜单类型"], row["图标"]
                    m.perms = row.get("权限标识", "")
                    self.session.add(m)
        else:
            self.stdout.write("使用内置默认菜单配置...\n")
            for m_def in DEFAULT_MENUS:
                m = self.session.query(SysMenu).get(m_def["id"]) or SysMenu(id=m_def["id"])
                m.menu_name, m.parent_id = m_def["name"], (m_def["pid"] if m_def["pid"] != 0 else None)
                m.path, m.menu_type, m.icon, m.perms = m_def["path"], m_def["type"], m_def["icon"], m_def["perm"]
                self.session.add(m)
        self.session.flush()

    def _load_roles(self):
        csv_path = Path("docs/assets/sample_data/sys_roles.csv")
        if csv_path.exists():
            self.stdout.write("从 CSV 加载角色配置...\n")
            with open(csv_path, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    rid = int(row["ID"])
                    r = self.session.query(SysRole).get(rid) or SysRole(id=rid)
                    r.role_name, r.role_key, r.data_scope = row["角色名称"], row["角色键"], int(row["数据范围"])
                    self.session.add(r)
        else:
            self.stdout.write("使用内置默认角色配置...\n")
            for r_def in DEFAULT_ROLES:
                r = self.session.query(SysRole).get(r_def["id"]) or SysRole(id=r_def["id"])
                r.role_name, r.role_key, r.data_scope = r_def["name"], r_def["key"], r_def["scope"]
                self.session.add(r)
        self.session.flush()
