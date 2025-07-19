"""
内容生成代理 (ContentGeneratorAgent)

职责：
1. 分析收集到的完美上下文
2. 生成高质量的章节内容
3. 进行多轮质量检查和改进
4. 确保内容的连贯性和准确性
5. 计算和优化内容质量评分
"""

from .simple_agent import SimpleContentGeneratorAgent

# 提供向后兼容性
ContentGeneratorAgent = SimpleContentGeneratorAgent

__all__ = ['ContentGeneratorAgent', 'SimpleContentGeneratorAgent'] 