"""
章节写作代理 (ReactAgent)

基于ReAct(Reasoning-Acting-Observing)框架的智能写作Agent

核心特性：
1. 完整的推理-行动-观察循环
2. 结果质量评估和反馈机制
3. 自适应查询优化策略
4. 从检索失败中学习改进
5. 支持多种文档类型
6. 迭代直到获得满意结果

职责：
1. 分析章节信息需求并制定检索策略
2. 执行多轮RAG检索优化
3. 评估检索结果质量
4. 基于反馈调整查询方法
5. 综合高质量信息生成内容
"""

from .react_agent import ReactAgent

__all__ = [
    'ReactAgent',           # 🌟 唯一的ReAct智能Agent
] 