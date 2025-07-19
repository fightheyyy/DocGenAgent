#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gauz文档Agent - 智能长文档生成系统
主程序入口

基于多Agent架构的智能文档生成系统，支持从用户查询到完整文档的全流程自动化生成。

系统架构：
1. OrchestratorAgent - 编排代理：分析需求，生成文档结构和写作指导
2. SectionWriterAgent - 章节写作代理：使用ReAct框架智能检索相关资料
3. ContentGeneratorAgent - 内容生成代理：基于结构和资料生成最终文档

使用方法：
    python main.py [选项]
    
选项：
    --query "查询内容"    直接指定文档需求
    --interactive       进入交互模式
    --help             显示帮助信息
"""

import sys
import os
import json
import argparse
import time
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from clients.openrouter_client import OpenRouterClient
    from clients.simple_rag_client import SimpleRAGClient
    from Document_Agent.orchestrator_agent.agent import OrchestratorAgent
    from Document_Agent.section_writer_agent.react_agent import ReactAgent
    from Document_Agent.content_generator_agent.main_generator import MainDocumentGenerator
    from config.settings import setup_logging, get_config, get_concurrency_manager
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保您在项目根目录下运行此程序，并安装了所有依赖。")
    sys.exit(1)


class DocumentGenerationPipeline:
    """文档生成流水线 - 整合三个Agent的完整工作流，支持统一并发管理"""
    
    def __init__(self):
        """初始化流水线"""
        print("🔧 正在初始化文档生成系统...")
        
        # 设置日志
        setup_logging()
        
        # 初始化并发管理器
        self.concurrency_manager = get_concurrency_manager()
        
        # 初始化客户端
        try:
            self.llm_client = OpenRouterClient()
            self.rag_client = SimpleRAGClient()
            
            # 初始化三个Agent，传入统一的并发管理器
            self.orchestrator = OrchestratorAgent(self.rag_client, self.llm_client, self.concurrency_manager)
            self.section_writer = ReactAgent(self.llm_client, self.concurrency_manager)
            self.content_generator = MainDocumentGenerator(self.concurrency_manager)
            
            print("✅ 系统初始化成功！")
            self._print_concurrency_settings()
            
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            raise
    
    def _print_concurrency_settings(self):
        """打印当前并发设置"""
        print("\n" + "="*60)
        self.concurrency_manager.print_settings()
        print("="*60 + "\n")
    
    def set_concurrency(self, orchestrator_workers: int = None, react_workers: int = None, 
                       content_workers: int = None, rate_delay: float = None):
        """
        统一设置并发参数
        
        Args:
            orchestrator_workers: 编排代理线程数
            react_workers: 检索代理线程数
            content_workers: 内容生成代理线程数
            rate_delay: 请求间隔时间(秒)
        """
        print("🔧 更新并发设置...")
        
        if orchestrator_workers is not None:
            self.orchestrator.set_max_workers(orchestrator_workers)
            
        if react_workers is not None:
            self.section_writer.set_max_workers(react_workers)
            
        if content_workers is not None:
            self.content_generator.set_max_workers(content_workers)
            
        if rate_delay is not None:
            self.content_generator.set_rate_limit_delay(rate_delay)
            
        print("✅ 并发设置更新完成！")
        self._print_concurrency_settings()
    
    def get_concurrency_settings(self) -> dict:
        """获取当前并发设置"""
        return {
            'orchestrator_workers': self.orchestrator.get_max_workers(),
            'react_workers': self.section_writer.get_max_workers(),
            'content_workers': self.content_generator.get_max_workers(),
            'rate_delay': self.content_generator.get_rate_limit_delay()
        }
    
    def generate_document(self, user_query: str, output_dir: str = "outputs") -> Dict[str, str]:
        """
        完整文档生成流程
        
        Args:
            user_query: 用户需求描述
            output_dir: 输出目录
            
        Returns:
            Dict: 包含生成文件路径的字典
        """
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("🚀 开始文档生成流程...")
        print("=" * 80)
        print(f"📝 用户需求：{user_query}")
        print("=" * 80)
        
        try:
            # 阶段1：生成文档结构（OrchestratorAgent）
            print("\n🏗️  阶段1：生成文档结构和写作指导...")
            step1_start = time.time()
            
            document_guide = self.orchestrator.generate_complete_guide(user_query)
            
            step1_time = time.time() - step1_start
            sections_count = sum(len(part.get('sections', [])) for part in document_guide.get('report_guide', []))
            
            print(f"✅ 文档结构生成完成！")
            print(f"   📊 生成了 {len(document_guide.get('report_guide', []))} 个主要部分，{sections_count} 个子章节")
            print(f"   ⏱️  耗时：{step1_time:.1f}秒")
            
            # 保存阶段1结果
            step1_file = os.path.join(output_dir, f"step1_document_guide_{timestamp}.json")
            with open(step1_file, 'w', encoding='utf-8') as f:
                json.dump(document_guide, f, ensure_ascii=False, indent=2)
            
            # 阶段2：智能检索相关资料（SectionWriterAgent）
            print("\n🔍 阶段2：为各章节智能检索相关资料...")
            step2_start = time.time()
            
            enriched_guide = self.section_writer.process_report_guide(document_guide)
            
            step2_time = time.time() - step2_start
            print(f"✅ 资料检索完成！")
            print(f"   🔍 为 {sections_count} 个章节检索了相关资料")
            print(f"   ⏱️  耗时：{step2_time:.1f}秒")
            
            # 保存阶段2结果
            step2_file = os.path.join(output_dir, f"step2_enriched_guide_{timestamp}.json")
            with open(step2_file, 'w', encoding='utf-8') as f:
                json.dump(enriched_guide, f, ensure_ascii=False, indent=2)
            
            # 阶段3：生成最终文档（ContentGeneratorAgent）
            print("\n📝 阶段3：生成最终文档内容...")
            step3_start = time.time()
            
            # 保存为content_generator能识别的文件名
            generation_input = os.path.join(output_dir, f"生成文档的依据_{timestamp}.json")
            with open(generation_input, 'w', encoding='utf-8') as f:
                json.dump(enriched_guide, f, ensure_ascii=False, indent=2)
            
            # 生成最终文档
            final_doc_path = self.content_generator.generate_document(generation_input)
            
            step3_time = time.time() - step3_start
            print(f"✅ 最终文档生成完成！")
            print(f"   ⏱️  耗时：{step3_time:.1f}秒")
            
            # 计算总耗时
            total_time = step1_time + step2_time + step3_time
            print("\n" + "=" * 80)
            print("🎉 文档生成流程全部完成！")
            print(f"📊 总体统计：")
            print(f"   📑 主要部分：{len(document_guide.get('report_guide', []))} 个")
            print(f"   📄 子章节：{sections_count} 个")
            print(f"   ⏱️  总耗时：{total_time:.1f}秒")
            print("=" * 80)
            
            # 返回生成的文件路径
            return {
                'document_guide': step1_file,
                'enriched_guide': step2_file,
                'generation_input': generation_input,
                'final_document': final_doc_path,
                'output_directory': output_dir
            }
            
        except Exception as e:
            print(f"❌ 文档生成过程中出现错误: {e}")
            raise


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        Gauz文档Agent - 智能长文档生成系统                        ║
║                                                                              ║
║  🤖 基于多Agent架构的智能文档生成系统                                            ║
║  📝 支持从查询到完整文档的全流程自动化生成                                        ║
║  🚀 集成结构规划、智能检索、内容生成三大核心功能                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def interactive_mode():
    """交互模式"""
    print("\n🎮 进入交互模式")
    print("💡 您可以输入任何文档需求，系统将为您自动生成完整的专业文档")
    print("📌 支持的文档类型：评估报告、分析报告、方案书、技术文档等")
    print("⚡ 输入 'quit' 或 'exit' 退出程序")
    
    pipeline = DocumentGenerationPipeline()
    
    while True:
        print("\n" + "-" * 60)
        user_input = input("📝 请描述您需要生成的文档：").strip()
        
        if user_input.lower() in ['quit', 'exit', '退出', 'q']:
            print("👋 感谢使用Gauz文档Agent，再见！")
            break
            
        if not user_input:
            print("❌ 请输入有效的文档描述")
            continue
        
        try:
            # 生成文档
            result_files = pipeline.generate_document(user_input)
            
            print(f"\n📁 生成的文件：")
            for file_type, file_path in result_files.items():
                if file_type != 'output_directory':
                    print(f"   {file_type}: {file_path}")
            
            print(f"\n✨ 您可以在 '{result_files['output_directory']}' 目录下查看所有生成的文件")
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            print("💡 请尝试重新描述您的需求或检查系统配置")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Gauz文档Agent - 智能长文档生成系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --interactive
  python main.py --query "为城市更新项目编写环境影响评估报告"
  python main.py --query "白云区文物保护影响评估报告" --output outputs/heritage
        """
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='直接指定文档生成需求'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='进入交互模式'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='outputs',
        help='指定输出目录（默认：outputs）'
    )
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 检查参数
    if not args.query and not args.interactive:
        print("💡 请使用 --query 指定需求或使用 --interactive 进入交互模式")
        print("📖 使用 --help 查看详细帮助信息")
        return
    
    try:
        if args.interactive:
            # 交互模式
            interactive_mode()
        else:
            # 直接生成模式
            print(f"🎯 直接生成模式")
            pipeline = DocumentGenerationPipeline()
            result_files = pipeline.generate_document(args.query, args.output)
            
            print(f"\n📁 文档已生成到目录：{result_files['output_directory']}")
            print(f"📄 最终文档：{result_files['final_document']}")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 