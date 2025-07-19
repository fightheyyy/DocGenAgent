"""
编排代理 (OrchestratorAgent)

职责：
1. 分析文档生成目标和需求
2. 解析源文档结构和内容
3. 生成详细的文档大纲
4. 将任务分解为具体的章节规格
5. 协调整个生成流程
"""

from .agent import OrchestratorAgent

__all__ = ['OrchestratorAgent'] 