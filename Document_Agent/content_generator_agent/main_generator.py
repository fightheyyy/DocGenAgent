#!/usr/bin/env python3
"""
简化文档生成器 - 主程序

功能：
- 读取JSON文件（生成文档的依据.json）
- 支持统一的并发管理
- 只生成正文内容（不包含标题）
- 输出完整版markdown文档（无首行缩进）
"""

import json
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

# 确保可以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .simple_agent import SimpleContentGeneratorAgent
from clients.openrouter_client import OpenRouterClient
from config.settings import setup_logging, get_concurrency_manager, ConcurrencyManager


class MainDocumentGenerator:
    """主文档生成器 - 支持统一的并发管理"""
    
    def __init__(self, concurrency_manager: ConcurrencyManager = None):
        # 设置日志
        setup_logging()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 初始化LLM客户端和Agent
        self.llm_client = OpenRouterClient()
        self.agent = SimpleContentGeneratorAgent(self.llm_client)
        
        # 并发管理器
        self.concurrency_manager = concurrency_manager or get_concurrency_manager()
        self.max_workers = self.concurrency_manager.get_max_workers('content_generator_agent')
        self.rate_limit_delay = self.concurrency_manager.get_rate_limit_delay()
        
        # 速率控制
        self.last_request_time = 0
        self.request_lock = threading.Lock()
        
        self.logger.info(f"MainDocumentGenerator 初始化完成，并发线程数: {self.max_workers}, 速率限制: {self.rate_limit_delay}秒")

    def set_max_workers(self, max_workers: int):
        """动态设置最大线程数"""
        self.max_workers = max_workers
        self.concurrency_manager.set_max_workers('content_generator_agent', max_workers)
        self.logger.info(f"ContentGeneratorAgent 线程数已更新为: {max_workers}")

    def get_max_workers(self) -> int:
        """获取当前最大线程数"""
        return self.max_workers

    def set_rate_limit_delay(self, delay: float):
        """动态设置速率限制延迟"""
        self.rate_limit_delay = delay
        self.concurrency_manager.set_rate_limit_delay(delay)
        self.logger.info(f"ContentGeneratorAgent 速率限制已更新为: {delay}秒")

    def get_rate_limit_delay(self) -> float:
        """获取当前速率限制延迟"""
        return self.rate_limit_delay

    def generate_document(self, json_file_path: str = "第二agent的输出_刘氏宗祠_rag.json") -> str:
        """
        生成文档
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            str: 完整版文档路径
        """
        
        print("🚀 开始生成文档...")
        print(f"📁 输入文件: {json_file_path}")
        print(f"🔧 并行线程: {self.max_workers}")
        print(f"⏱️  速率限制: {self.rate_limit_delay}秒/请求")
        print("=" * 60)
        
        # 1. 检查文件
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"文件不存在: {json_file_path}")
        
        # 2. 读取JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # 3. 并行生成内容
        updated_json = self._generate_content_parallel(json_data)
        
        # 4. 保存JSON和生成markdown
        return self._save_results(updated_json)
    
    def _generate_content_parallel(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """并行生成内容"""
        
        print("⚡ 开始并行生成...")
        
        updated_json = json_data.copy()
        report_guide = updated_json.get('report_guide', [])
        
        # 准备任务列表
        tasks = []
        for title_idx, title_section in enumerate(report_guide):
            sections = title_section.get('sections', [])
            for section_idx, section in enumerate(sections):
                task = {
                    'title_idx': title_idx,
                    'section_idx': section_idx,
                    'subtitle': section.get('subtitle', ''),
                    'how_to_write': section.get('how_to_write', ''),
                    'retrieved_data': section.get('retrieved_data', ''),
                    'title': title_section.get('title', '')
                }
                tasks.append(task)
        
        total_tasks = len(tasks)
        completed_tasks = 0
        
        print(f"📋 总任务数: {total_tasks}")
        
        # 并行执行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self._generate_single_section, task): task
                for task in tasks
            }
            
            # 收集结果
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    
                    # 更新JSON
                    title_idx = task['title_idx']
                    section_idx = task['section_idx']
                    section = updated_json['report_guide'][title_idx]['sections'][section_idx]
                    
                    section['generated_content'] = result['content']
                    section['quality_score'] = result['quality_score']
                    section['word_count'] = result['word_count']
                    section['generation_time'] = result['generation_time']
                    
                    completed_tasks += 1
                    progress = (completed_tasks / total_tasks) * 100
                    
                    print(f"✅ [{completed_tasks:2d}/{total_tasks}] {progress:5.1f}% | {task['subtitle'][:20]:<20} | {result['word_count']:4d}字 | 质量:{result['quality_score']:.2f}")
                    
                except Exception as e:
                    completed_tasks += 1
                    print(f"❌ [{completed_tasks:2d}/{total_tasks}] 失败 | {task['subtitle'][:20]:<20} | 错误: {e}")
        
        print("🎉 并行生成完成!")
        return updated_json
    
    def _generate_single_section(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """生成单个章节（带速率限制）"""
        
        # 速率限制
        with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
        
        # 生成内容
        return self.agent.generate_content_from_json(
            task['subtitle'],
            task['how_to_write'],
            task['retrieved_data']
        )
    
    def _save_results(self, updated_json: Dict[str, Any]) -> str:
        """保存结果文件"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON
        json_path = f"生成文档的依据_完成_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(updated_json, f, ensure_ascii=False, indent=2)
        
        # 生成markdown
        full_md_path = f"完整版文档_{timestamp}.md"
        
        # 完整版
        full_content = self._convert_to_markdown(updated_json)
        with open(full_md_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        # 统计信息
        stats = self._get_stats(updated_json)
        
        print("=" * 60)
        print("📊 生成统计:")
        print(f"   总章节数: {stats['total_sections']}")
        print(f"   完成章节: {stats['completed_sections']}")
        print(f"   总字数: {stats['total_words']:,}")
        print(f"   平均质量分: {stats['average_quality']:.3f}")
        print("=" * 60)
        print("📁 输出文件:")
        print(f"   JSON: {json_path}")
        print(f"   完整版: {full_md_path}")
        print("=" * 60)
        
        return full_md_path
    
    def _convert_to_markdown(self, json_data: Dict[str, Any]) -> str:
        """转换为markdown格式"""
        
        markdown_lines = []
        report_guide = json_data.get('report_guide', [])
        
        for title_section in report_guide:
            title = title_section.get('title', '')
            sections = title_section.get('sections', [])
            
            # 添加主标题（一级标题）
            markdown_lines.append(f"# {title}")
            markdown_lines.append("")
            
            # 处理每个子节
            for section in sections:
                subtitle = section.get('subtitle', '')
                generated_content = section.get('generated_content', '')
                
                # 添加子标题（二级标题）
                markdown_lines.append(f"## {subtitle}")
                markdown_lines.append("")
                
                # 添加生成的内容（只有正文，不包含标题）
                if generated_content:
                    # 对正文内容进行缩进处理
                    content = self._format_content(generated_content)
                    markdown_lines.append(content)
                else:
                    markdown_lines.append("*[内容未生成]*")
                
                markdown_lines.append("")
        
        return "\n".join(markdown_lines)
    
    def _format_content(self, content: str) -> str:
        """对正文内容进行格式化（无缩进）"""
        
        if not content:
            return content
        
        # 直接返回原内容，不进行缩进处理
        return content
    
    def _get_stats(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取统计信息"""
        
        stats = {
            'total_sections': 0,
            'completed_sections': 0,
            'total_words': 0,
            'average_quality': 0.0
        }
        
        report_guide = json_data.get('report_guide', [])
        quality_scores = []
        
        for title_section in report_guide:
            sections = title_section.get('sections', [])
            stats['total_sections'] += len(sections)
            
            for section in sections:
                if 'generated_content' in section:
                    stats['completed_sections'] += 1
                    stats['total_words'] += section.get('word_count', 0)
                    
                    quality_score = section.get('quality_score', 0.0)
                    quality_scores.append(quality_score)
        
        if quality_scores:
            stats['average_quality'] = sum(quality_scores) / len(quality_scores)
        
        return stats


def main():
    """主函数"""
    
    try:
        # 创建生成器
        generator = MainDocumentGenerator()
        
        # 生成文档
        full_path = generator.generate_document()
        
        print("🎉 文档生成完成!")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 