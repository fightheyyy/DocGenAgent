"""
ReAct Agent - 实现完整的Reasoning-Acting-Observing循环

此版本将并行处理逻辑封装在Agent内部，调用方只需调用一个方法即可处理整个报告。
支持统一的并发管理。
"""

import json
import logging
import re
import requests
import sys
import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import concurrent.futures

# 添加项目路径以导入 SimpleRAGClient 和 ConcurrencyManager
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from clients.simple_rag_client import SimpleRAGClient
from config.settings import get_concurrency_manager, ConcurrencyManager

# ==============================================================================
# 1. 数据结构与辅助类
# ==============================================================================

class SectionInfo:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

@dataclass
class ReActState:
    iteration: int = 0
    attempted_queries: List[str] = field(default_factory=list)
    retrieved_results: List[Dict] = field(default_factory=list)
    quality_scores: List[float] = field(default_factory=list)

class ColoredLogger:
    COLORS = {
        'RESET': '\033[0m', 'BLUE': '\033[94m', 'GREEN': '\033[92m', 
        'YELLOW': '\033[93m', 'RED': '\033[91m', 'PURPLE': '\033[95m', 
        'CYAN': '\033[96m', 'WHITE': '\033[97m',
    }
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _colorize(self, text: str, color: str) -> str:
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['RESET']}"
    
    def info(self, message: str): self.logger.info(message)
    def error(self, message: str): self.logger.error(message)
    def warning(self, message: str): self.logger.warning(message)
    def debug(self, message: str): self.logger.debug(message)
    def thought(self, content: str): self.logger.info(self._colorize(f"💭 Thought: {content}", 'BLUE'))
    def input_tool(self, content: str): self.logger.info(self._colorize(f"🔧 Input: {content}", 'GREEN'))
    def observation(self, content: str): self.logger.info(self._colorize(f"👁️ Observation: {content}", 'YELLOW'))
    def reflection(self, content: str): self.logger.info(self._colorize(f"🤔 Reflection: {content}", 'CYAN'))
    def section_start(self, title: str): self.logger.info(self._colorize(f"\n📝 开始处理章节: {title}", 'PURPLE'))
    def section_complete(self, title: str, iterations: int, quality: float): self.logger.info(self._colorize(f"✅ 章节'{title}'完成 | 迭代{iterations}次 | 最终质量: {quality:.2f}", 'WHITE'))
    def iteration(self, current: int, total: int): self.logger.info(self._colorize(f"🔄 [Iteration {current}/{total}]", 'CYAN'))

# ==============================================================================
# 2. 核心Agent类
# ==============================================================================

class ReactAgent:
    def __init__(self, client: Any, concurrency_manager: ConcurrencyManager = None):
        self.client = client
        self.colored_logger = ColoredLogger(__name__)
        self.max_iterations = 3
        self.quality_threshold = 0.7
        self.rag_retriever = SimpleRAGClient()
        
        # 并发管理器
        self.concurrency_manager = concurrency_manager or get_concurrency_manager()
        self.max_workers = self.concurrency_manager.get_max_workers('react_agent')
        
        self.query_strategies = {
            'direct': "直接使用核心关键词搜索", 
            'contextual': "结合写作指导上下文的详细查询", 
            'semantic': "搜索与主题相关的语义概念", 
            'specific': "搜索具体的案例、数据或技术标准",
            'alternative': "使用同义词和相关概念进行发散搜索"
        }
        
        self.colored_logger.info(f"ReactAgent 初始化完成，并发线程数: {self.max_workers}")

    def set_max_workers(self, max_workers: int):
        """动态设置最大线程数"""
        self.max_workers = max_workers
        self.concurrency_manager.set_max_workers('react_agent', max_workers)
        self.colored_logger.info(f"ReactAgent 线程数已更新为: {max_workers}")

    def get_max_workers(self) -> int:
        """获取当前最大线程数"""
        return self.max_workers

    def process_report_guide(self, report_guide_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理完整的报告指南 - 主入口 (并行处理)"""
        self.colored_logger.logger.info(f"🤖 ReAct开始并行处理报告指南... (线程数: {self.max_workers})")
        result_data = json.loads(json.dumps(report_guide_data))
        
        tasks = []
        for part in result_data.get('report_guide', []):
            part_context = {'title': part.get('title', ''), 'goal': part.get('goal', '')}
            for section in part.get('sections', []):
                tasks.append((section, part_context))

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_section = {
                executor.submit(self._process_section_with_react, section, part_context): section
                for section, part_context in tasks
            }
            for future in concurrent.futures.as_completed(future_to_section):
                section = future_to_section[future]
                try:
                    section['retrieved_data'] = future.result()
                except Exception as exc:
                    error_message = f"章节 '{section.get('subtitle')}' 在并行处理中发生错误: {exc}"
                    self.colored_logger.error(error_message)
                    section['retrieved_data'] = error_message
        
        self.colored_logger.logger.info("\n✅ 所有章节并行处理完成！")
        return result_data

    def _process_section_with_react(self, section_data: dict, part_context: dict) -> str:
        """为单个章节启动并管理ReAct处理流程。"""
        subtitle = section_data.get('subtitle', '')
        self.colored_logger.section_start(subtitle)
        state = ReActState()
        section_context = {
            'subtitle': subtitle, 'how_to_write': section_data.get('how_to_write', ''),
            'part_title': part_context.get('title', ''), 'part_goal': part_context.get('goal', '')
        }
        retrieved_content = self._react_loop_for_section(section_context, state)
        self.colored_logger.section_complete(subtitle, state.iteration, max(state.quality_scores) if state.quality_scores else 0)
        return retrieved_content

    def _react_loop_for_section(self, section_context: Dict[str, str], state: ReActState) -> str:
        """ReAct的核心循环"""
        while state.iteration < self.max_iterations:
            state.iteration += 1
            self.colored_logger.iteration(state.iteration, self.max_iterations)
            
            action_plan = self._reason_and_act_for_section(section_context, state)
            if not action_plan or not action_plan.get('keywords'):
                self.colored_logger.thought("未能生成有效的行动计划，提前结束。")
                break

            reasoning, query, strategy = (action_plan.get('analysis'), action_plan.get('keywords'), action_plan.get('strategy'))
            state.attempted_queries.append(f"{strategy}:{query}")
            self.colored_logger.thought(reasoning)
            self.colored_logger.input_tool(f"SimpleRAGClient | Strategy: {strategy} | Query: {query}")
            
            results, quality_score = self._observe_section_results(query, section_context)
            state.retrieved_results.extend(results)
            state.quality_scores.append(quality_score)
            self.colored_logger.observation(f"检索到 {len(results)} 条结果, 评估质量分: {quality_score:.2f}")
            
            if not self._reflect(state, quality_score): break
                
        return self._synthesize_retrieved_content(section_context, state)

    def _reason_and_act_for_section(self, section_context: Dict[str, str], state: ReActState) -> Optional[Dict[str, str]]:
        """合并推理和行动阶段"""
        used_strategies = {q.split(':')[0] for q in state.attempted_queries if ':' in q}
        available_strategies = {k: v for k, v in self.query_strategies.items() if k not in used_strategies} or self.query_strategies
        prompt = f"""
作为一名专业的信息检索分析师，为报告章节制定检索计划。
【目标章节】: {section_context['subtitle']}
【写作指导】: {section_context['how_to_write']}
【历史尝试】: 已尝试查询: {state.attempted_queries[-3:]}, 历史质量: {state.quality_scores[-3:]}
【可用策略】: {json.dumps(available_strategies, ensure_ascii=False)}
【任务】: 1.分析现状。2.选择一个最佳策略。3.生成3-5个关键词。
【输出格式】: 必须严格返回以下JSON格式:
{{
  "analysis": "简要分析（100字内）",
  "strategy": "选择的策略名称",
  "keywords": "用逗号分隔的关键词"
}}"""
        try:
            response_str = self.client.generate(prompt)
            match = re.search(r'\{.*\}', response_str, re.DOTALL)
            action_plan = json.loads(match.group(0))
            if all(k in action_plan for k in ['analysis', 'strategy', 'keywords']):
                return action_plan
            self.colored_logger.error(f"LLM返回的JSON格式不完整: {action_plan}")
            return None
        except Exception as e:
            self.colored_logger.error(f"推理与行动阶段出错: {e}")
            return None

    def _observe_section_results(self, query: str, section_context: Dict[str, str]) -> Tuple[List[Dict], float]:
        """观察阶段"""
        try:
            keywords = [k.strip() for k in query.replace('，', ',').split(',') if k.strip()]
            combined_query = " ".join(keywords[:3])
            all_results = self.rag_retriever.execute(combined_query) if combined_query else []
            quality_score = self._evaluate_section_results_quality(all_results, section_context, query)
            return all_results, quality_score
        except Exception as e:
            self.colored_logger.error(f"观察阶段失败: {e}")
            return [], 0.0

    def _evaluate_section_results_quality(self, results: List[Dict], section_context: Dict[str, str], query: str) -> float:
        """评估结果质量"""
        if not results: return 0.0
        evaluation_prompt = f"""
评估以下检索结果对章节写作的适用性：
【目标章节】: {section_context['subtitle']}
【写作指导】: {section_context['how_to_write']}
【本次查询】: {query}
【检索结果】: {chr(10).join(f"- {str(r.get('content', r))[:150]}..." for r in results[:3])}
【要求】: 综合评估后，只返回一个0.0到1.0的小数评分。"""
        try:
            response = self.client.generate(evaluation_prompt)
            score_match = re.search(r'0?\.\d+|[01]', response)
            return max(0.0, min(1.0, float(score_match.group()))) if score_match else 0.2
        except Exception: return 0.1

    def _reflect(self, state: ReActState, current_quality: float) -> bool:
        """反思阶段"""
        if current_quality >= self.quality_threshold:
            self.colored_logger.reflection(f"质量分 {current_quality:.2f} 达标, 停止。")
            return False
        if state.iteration >= self.max_iterations:
            self.colored_logger.reflection(f"达到最大迭代次数, 停止。")
            return False
        if len(state.quality_scores) >= 2 and all(s < 0.3 for s in state.quality_scores[-2:]):
            self.colored_logger.reflection("质量分持续过低, 提前停止。")
            return False
        return True

    def _synthesize_retrieved_content(self, section_context: Dict[str, str], state: ReActState) -> str:
        """合成最终内容"""
        if not state.retrieved_results: return f"未能检索到关于'{section_context['subtitle']}'的相关信息。"
        unique_contents = {str(r.get('content', str(r)))[:50]: (str(r.get('content', str(r))), r.get('source', '未知')) for r in state.retrieved_results}
        return "\n---\n".join([f"来源: {s}\n内容: {c[:300]}...\n" for c, s in unique_contents.values()][:5])
