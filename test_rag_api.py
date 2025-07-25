#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的RAG检索API调用

演示如何使用修改后的ExternalAPIClient调用localhost:8000的RAG检索服务
"""

import asyncio
import json
from clients.external_api_client import ExternalAPIClient

def test_rag_search():
    """测试RAG检索功能"""
    print("🧪 测试新的RAG检索API调用")
    print("=" * 50)
    
    # 初始化客户端
    client = ExternalAPIClient()
    
    # 打印服务状态
    print("📊 服务状态:")
    status = client.check_service_status()
    print(f"   模板搜索服务: {status['template_api_url']} - {'可用' if status['tools']['template_search']['available'] else '不可用'}")
    print(f"   RAG检索服务: {status['rag_api_url']} - {'可用' if status['tools']['rag_search']['available'] else '不可用'}")
    
    # 测试RAG检索
    print("\n🔍 测试RAG检索...")
    print("ℹ️ 注意: 此测试需要localhost:8000上有RAG检索服务运行")
    try:
        result = client.document_search(
            query_text="医灵古庙的地理位置",
            project_name="医灵古庙",
            top_k=5
        )
        
        if result:
            print("✅ RAG检索成功！")
            print(f"📄 检索到的文本数量: {len(result.get('retrieved_text', []))}")
            print(f"🖼️ 检索到的图片数量: {len(result.get('retrieved_image', []))}")
            print(f"📊 元数据: {result.get('metadata', {})}")
            
            # 显示部分文本内容
            if result.get('retrieved_text'):
                text_content = result['retrieved_text'][0] if result['retrieved_text'] else ""
                if text_content:
                    preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                    print(f"📝 文本预览: {preview}")
        else:
            print("❌ RAG检索失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    
    print("\n🔧 API请求格式示例:")
    print("""
POST http://localhost:8000/api/v1/search
Content-Type: application/json

{
  "query": "医灵古庙的地理位置",
  "project_name": "医灵古庙",
  "search_type": "hybrid",
  "top_k": 5
}
    """)
    
    print("📋 预期响应格式:")
    print("""
{
  "status": "success",
  "message": "搜索完成",
  "data": {
    "retrieved_text": "...",
    "retrieved_images": [...],
    "metadata": {...}
  }
}
    """)

if __name__ == "__main__":
    test_rag_search() 