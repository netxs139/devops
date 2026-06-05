"""Calendar dimension master data (MDM_CALENDAR) initialization command."""

from datetime import date
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.calendar_service import CalendarService


class Command(BaseCommand):
    """Initialize the MDM_CALENDAR time-dimension table for a given year range."""

    help = "日历与时间维度主数据 (MDM_CALENDAR) 初始化"

    def handle(
        self,
        session: Session,
        start_year: Annotated[int, typer.Option("--start-year", help="起始年份")] = 2024,
        end_year: Annotated[int, typer.Option("--end-year", help="结束年份")] = 2026,
    ):
        """Generate calendar rows for each day between start_year and end_year."""
        service = CalendarService(session)

        try:
            self.stdout.write(f"正在初始化日历数据从 {start_year} 到 {end_year} (via Service)...\n")

            total_days = (date(end_year, 12, 31) - date(start_year, 1, 1)).days + 1

            with self.get_progress() as progress:
                task = progress.add_task("[cyan]生成日历维度...", total=total_days)
                count = service.generate_calendar_data(start_year, end_year, progress_callback=lambda: progress.advance(task))

            self.stdout.write(f"✅ 日历数据初始化完成，新增 {count} 条记录。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 日历初始化失败: {e}\n")
            return False
