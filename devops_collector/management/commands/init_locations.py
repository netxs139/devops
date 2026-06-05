"""Geographic location master data (mdm_locations) initialization command."""

import logging

from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.location_service import LocationService


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Initialize base geographic location records via LocationService."""

    help = "初始化地理位置主数据 (mdm_locations)"

    def handle(self, session: Session):
        """Call LocationService to seed base location records."""
        service = LocationService(session)

        try:
            self.stdout.write("开始初始化位置主数据...\n")
            service.init_base_locations()
            self.stdout.write("✅ 位置主数据初始化完成。\n")
            return True

        except Exception as e:
            logger.error(f"位置初始化失败: {e}")
            self.stderr.write(f"❌ 位置初始化失败: {e}\n")
            return False
