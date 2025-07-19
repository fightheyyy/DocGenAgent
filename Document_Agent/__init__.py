"""
多Agent文档生成系统

包含三个专门的Agent：
1. OrchestratorAgent - 编排代理
2. SectionWriterAgent - 章节写作代理  
3. ContentGeneratorAgent - 内容生成代理
"""

from .orchestrator_agent.agent import OrchestratorAgent
from .section_writer_agent.react_agent import ReactAgent
from .content_generator_agent.main_generator import MainDocumentGenerator

__all__ = [
    'OrchestratorAgent',
    'ReactAgent', 
    'MainDocumentGenerator'
] 