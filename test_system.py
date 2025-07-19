#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本

用于快速验证Gauz文档Agent系统是否能正常工作
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("🔧 测试模块导入...")
    
    try:
        from clients.openrouter_client import OpenRouterClient
        print("✅ OpenRouterClient 导入成功")
    except ImportError as e:
        print(f"❌ OpenRouterClient 导入失败: {e}")
        return False
    
    try:
        from clients.simple_rag_client import SimpleRAGClient
        print("✅ SimpleRAGClient 导入成功")
    except ImportError as e:
        print(f"❌ SimpleRAGClient 导入失败: {e}")
        return False
    
    try:
        from Document_Agent.orchestrator_agent.agent import OrchestratorAgent
        print("✅ OrchestratorAgent 导入成功")
    except ImportError as e:
        print(f"❌ OrchestratorAgent 导入失败: {e}")
        return False
    
    try:
        from Document_Agent.section_writer_agent.react_agent import ReactAgent
        print("✅ ReactAgent 导入成功")
    except ImportError as e:
        print(f"❌ ReactAgent 导入失败: {e}")
        return False
    
    try:
        from Document_Agent.content_generator_agent.main_generator import MainDocumentGenerator
        print("✅ MainDocumentGenerator 导入成功")
    except ImportError as e:
        print(f"❌ MainDocumentGenerator 导入失败: {e}")
        return False
    
    try:
        from config.settings import setup_logging, get_config
        print("✅ config.settings 导入成功")
    except ImportError as e:
        print(f"❌ config.settings 导入失败: {e}")
        return False
    
    return True

def test_config():
    """测试配置"""
    print("\n⚙️ 测试系统配置...")
    
    try:
        from config.settings import get_config
        config = get_config()
        
        # 检查OpenRouter配置
        if 'openrouter' in config:
            print("✅ OpenRouter配置存在")
            openrouter_config = config['openrouter']
            if 'api_key' in openrouter_config and openrouter_config['api_key']:
                print("✅ API密钥已配置")
            else:
                print("⚠️ API密钥未配置或为空")
            
            if 'model' in openrouter_config:
                print(f"✅ 模型配置: {openrouter_config['model']}")
        else:
            print("❌ OpenRouter配置缺失")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_clients():
    """测试客户端连接"""
    print("\n🌐 测试客户端连接...")
    
    try:
        from clients.openrouter_client import OpenRouterClient
        from clients.simple_rag_client import SimpleRAGClient
        
        # 测试OpenRouter客户端
        print("  🔌 测试OpenRouter客户端...")
        llm_client = OpenRouterClient()
        print("  ✅ OpenRouter客户端创建成功")
        
        # 测试简单的API调用
        try:
            response = llm_client.generate("请回复'连接成功'", max_tokens=10)
            if response and "连接成功" in response:
                print("  ✅ OpenRouter API连接测试成功")
            else:
                print(f"  ⚠️ OpenRouter API响应异常: {response}")
        except Exception as e:
            print(f"  ⚠️ OpenRouter API连接测试失败: {e}")
        
        # 测试RAG客户端
        print("  🔌 测试RAG客户端...")
        rag_client = SimpleRAGClient()
        print("  ✅ RAG客户端创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 客户端测试失败: {e}")
        return False

def test_pipeline_creation():
    """测试流水线创建"""
    print("\n🏭 测试文档生成流水线创建...")
    
    try:
        from main import DocumentGenerationPipeline
        
        pipeline = DocumentGenerationPipeline()
        print("✅ DocumentGenerationPipeline 创建成功")
        
        # 检查组件是否正确初始化
        if hasattr(pipeline, 'orchestrator'):
            print("✅ OrchestratorAgent 初始化成功")
        else:
            print("❌ OrchestratorAgent 初始化失败")
            return False
            
        if hasattr(pipeline, 'section_writer'):
            print("✅ ReactAgent 初始化成功")
        else:
            print("❌ ReactAgent 初始化失败")
            return False
            
        if hasattr(pipeline, 'content_generator'):
            print("✅ MainDocumentGenerator 初始化成功")
        else:
            print("❌ MainDocumentGenerator 初始化失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 流水线创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 Gauz文档Agent 系统测试")
    print("=" * 60)
    
    all_passed = True
    
    # 测试1：模块导入
    if not test_imports():
        all_passed = False
    
    # 测试2：配置检查
    if not test_config():
        all_passed = False
    
    # 测试3：客户端连接
    if not test_clients():
        all_passed = False
    
    # 测试4：流水线创建
    if not test_pipeline_creation():
        all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！系统已准备就绪。")
        print("\n💡 您现在可以运行：")
        print("   python main.py --interactive")
        print("   python main.py --query '您的文档需求'")
    else:
        print("❌ 部分测试失败，请检查配置和依赖。")
        print("\n🔧 建议步骤：")
        print("   1. 确保在项目根目录下运行测试")
        print("   2. 检查网络连接")
        print("   3. 验证config/settings.py中的API配置")
        print("   4. 安装必要的依赖: pip install requests")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 