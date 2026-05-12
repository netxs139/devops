"""AI 效能归因分析模块。

使用 LiteLLM 封装对异常效能指标的自动诊断与归因分析。
"""

import logging
from typing import Any

from litellm import completion

from devops_collector.config import settings


logger = logging.getLogger(__name__)


class EfficacyAnalyzer:
    """研发效能 AI 归因分析器。"""

    def __init__(self):
        self.model = settings.ai.model or "gpt-4o-mini"
        self.api_key = settings.ai.api_key
        self.base_url = settings.ai.base_url

    def analyze_metrics(self, metrics_data: dict[str, Any]) -> str:
        """分析异常指标数据并生成归因报告。

        Args:
            metrics_data: 包含各项指标的字典（如缺陷密度、MTTR、代码翻动率等）。

        Returns:
            str: AI 生成的 Markdown 格式诊断报告。
        """
        if not self.api_key:
            return "⚠️ AI 配置缺失: 请在环境变量中配置 `DEVOPS__AI__API_KEY` 以激活该功能。"

        prompt = f"""
你是一名资深的 DevOps 效能专家与敏捷教练。
请基于以下最新的系统研发效能异常指标，出具一份不超过 300 字的专业诊断与归因报告。

要求：
1. 直击痛点，指出可能导致异常的根本原因。
2. 给出 1-2 条高价值的行动建议。
3. 务必使用 Markdown 格式（适当使用加粗或列表）。

【异常指标数据快照】
{metrics_data}
"""

        try:
            logger.info(f"正在呼叫 AI 模型 ({self.model}) 进行效能归因...")

            kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "api_key": self.api_key,
                "temperature": 0.2,
                "max_tokens": 1024,
            }
            if self.base_url and self.base_url != "https://api.openai.com/v1":
                kwargs["api_base"] = self.base_url
                # LiteLLM 遇到自定义 base_url 时，如果不带前缀，默认按 openai 协议处理最稳妥
                if "/" not in kwargs["model"]:
                    kwargs["model"] = f"openai/{self.model}"

            response = completion(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"AI 归因请求失败: {e}")
            return f"❌ AI 归因引擎异常: {str(e)}"
