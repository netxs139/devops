from datetime import date

from devops_collector.core.management import BaseCommand


class Command(BaseCommand):
    help = "日历与时间维度主数据 (MDM_CALENDAR) 初始化"

    def add_arguments(self, parser):
        parser.add_argument("--start-year", type=int, default=2024, help="起始年份 (默认: 2024)")
        parser.add_argument("--end-year", type=int, default=2026, help="结束年份 (默认: 2026)")

    def handle(self, *args, **options):
        start_year: int = options.get("start_year", 2024)
        end_year: int = options.get("end_year", 2026)

        from devops_collector.services.calendar_service import CalendarService

        service = CalendarService(self.session)

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
