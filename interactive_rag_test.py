#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式RAG测试工具
允许用户输入查询词来测试RAG检索功能
"""

import sys
import os
sys.path.append('.')
from clients.simple_rag_client import SimpleRAGClient
from Document_Agent.section_writer_agent.react_agent import ReactAgent
from clients.openrouter_client import OpenRouterClient
import json
import logging

# 设置简洁的日志
logging.basicConfig(level=logging.WARNING)

class InteractiveRAGTester:
    def __init__(self):
        print('🔧 初始化RAG测试工具...')
        self.rag_client = SimpleRAGClient()
        self.llm_client = OpenRouterClient()
        self.react_agent = ReactAgent(self.llm_client)
        print(f'📡 RAG端点: {self.rag_client.base_url}')
        print('✅ 初始化完成！\n')

    def test_basic_rag(self, query):
        """测试基础RAG检索"""
        print(f'🔍 基础RAG检索测试')
        print(f'查询: "{query}"')
        print('-' * 60)
        
        try:
            results = self.rag_client.execute(query)
            print(f'📬 找到 {len(results)} 条结果\n')
            
            if results:
                for i, result in enumerate(results):
                    print(f'📄 结果 {i+1}:')
                    if isinstance(result, dict):
                        for key, value in result.items():
                            print(f'  {key}: {type(value).__name__} (长度: {len(str(value))})')
                            if key == 'content':
                                # 显示内容
                                content_str = str(value)
                                if len(content_str) > 500:
                                    preview = content_str[:500] + '...'
                                else:
                                    preview = content_str
                                print(f'    内容: {preview}')
                            else:
                                print(f'    值: {value}')
                    else:
                        print(f'  内容: {result}')
                    print()
            else:
                print('📭 未找到任何结果')
                
        except Exception as e:
            print(f'❌ 检索失败: {e}')

    def test_react_agent(self, query, how_to_write=""):
        """测试ReactAgent完整流程"""
        print(f'🤖 ReactAgent完整流程测试')
        print(f'查询主题: "{query}"')
        if how_to_write:
            print(f'写作指导: "{how_to_write}"')
        print('-' * 60)
        
        # 构建测试数据
        test_data = {
            "report_guide": [{
                "title": "测试部分",
                "goal": "测试ReactAgent的RAG检索功能",
                "sections": [{
                    "subtitle": f"关于{query}的章节",
                    "how_to_write": how_to_write or f"请详细描述关于{query}的相关信息，包括背景、现状、影响等方面。"
                }]
            }]
        }
        
        try:
            print('🔄 开始ReactAgent处理...')
            result = self.react_agent.process_report_guide(test_data)
            
            # 显示结果
            section = result['report_guide'][0]['sections'][0]
            retrieved_data = section.get('retrieved_data', '')
            
            print(f'📝 检索结果长度: {len(retrieved_data)} 字符')
            print(f'📄 完整检索结果:')
            print('=' * 60)
            print(retrieved_data)
            print('=' * 60)
            
        except Exception as e:
            print(f'❌ ReactAgent处理失败: {e}')
            import traceback
            traceback.print_exc()

    def run_interactive_test(self):
        """运行交互式测试"""
        print('🎮 RAG交互式测试工具')
        print('=' * 60)
        print('命令说明:')
        print('  1. 输入查询词 -> 基础RAG检索')
        print('  2. react:查询词 -> ReactAgent完整流程')
        print('  3. react:查询词|写作指导 -> ReactAgent带自定义写作指导')
        print('  4. quit 或 exit -> 退出')
        print('=' * 60)
        
        while True:
            try:
                user_input = input('\n🔍 请输入查询 (或输入 quit 退出): ').strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print('👋 测试结束，再见！')
                    break
                
                if not user_input:
                    print('⚠️ 请输入有效的查询词')
                    continue
                
                print()  # 空行
                
                if user_input.startswith('react:'):
                    # ReactAgent测试
                    content = user_input[6:]  # 去掉 'react:' 前缀
                    
                    if '|' in content:
                        query, how_to_write = content.split('|', 1)
                        query = query.strip()
                        how_to_write = how_to_write.strip()
                    else:
                        query = content.strip()
                        how_to_write = ""
                    
                    self.test_react_agent(query, how_to_write)
                else:
                    # 基础RAG测试
                    self.test_basic_rag(user_input)
                
            except KeyboardInterrupt:
                print('\n👋 测试中断，再见！')
                break
            except Exception as e:
                print(f'❌ 发生错误: {e}')

def main():
    """主函数"""
    try:
        tester = InteractiveRAGTester()
        tester.run_interactive_test()
    except Exception as e:
        print(f'❌ 初始化失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 