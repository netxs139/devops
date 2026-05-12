"""AI 效能归因命令。"""

from devops_collector.core.management import BaseCommand, DiagHelper
from devops_collector.services.ai_analyzer import EfficacyAnalyzer


class Command(BaseCommand):
    help = "抓取系统效能异常指标，并使用大模型进行智能归因分析"

    def handle(self, *args, **options) -> bool | None:
        DiagHelper.print_header("AI 效能诊断与归因 (LiteLLM)")

        with self.get_progress() as progress:
            task = progress.add_task("[cyan]正在收集团队效能异常指标...", total=100)

            # 模拟抓取数据库中的异常指标组合
            # (高频的真实场景：缺陷密度偏高 + 修复时间长 + 代码翻动率剧烈)
            try:
                metrics = {
                    "project_name": "DevOps Core Services",
                    "sprint_duration_days": 14,
                    "defect_density": "8.5 bugs/KLOC",
                    "defect_density_status": "异常偏高 (历史基准为 2.1)",
                    "code_churn_rate": "42%",
                    "mean_time_to_resolve_bugs": "128 hours (劣化)",
                    "code_review_rejection_rate": "35%",
                }
                progress.update(task, advance=50, description="[cyan]指标收集完毕，正在呼叫 AI 大脑...")

                analyzer = EfficacyAnalyzer()
                report = analyzer.analyze_metrics(metrics)

                progress.update(task, advance=50, description="[green]AI 归因分析完成！")
            except Exception as e:
                self.stderr.write(f"执行失败: {e}\n")
                return False

        # 打印异常指标面板
        self.console.print("\n[bold yellow]🔍 异常指标快照:[/bold yellow]")
        for k, v in metrics.items():
            self.console.print(f"  - [dim]{k}:[/dim] [white]{v}[/white]")

        # 打印生成的 AI 报告
        self.console.print("\n[bold magenta]🤖 专家归因报告:[/bold magenta]")
        from rich.markdown import Markdown
        from rich.panel import Panel

        self.console.print(Panel(Markdown(report), title="[AI Diagnosis]", border_style="magenta", expand=False))

        DiagHelper.print_footer()
        return True
