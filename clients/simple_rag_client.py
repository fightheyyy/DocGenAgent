"""
简化的RAG客户端实现
"""

import requests
import logging
from typing import List, Dict, Any, Optional


class SimpleRAGClient:
    """简化的RAG客户端实现"""
    
    def __init__(self):
        self.base_url = "http://192.168.1.15:8000/rag_agent"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.timeout = 30
    
    def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """检索相关信息"""
        try:
            # 使用search接口
            payload = {"question": query}
            
            response = requests.post(self.base_url, json=payload, timeout=self.timeout, 
                                  headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            
            result_data = response.json()
            
            # 统一返回格式处理
            if isinstance(result_data, dict) and 'results' in result_data:
                results = result_data['results']
            elif isinstance(result_data, list):
                results = result_data
            else:
                results = [{'content': str(result_data), 'source': 'RAG检索'}]
            
            # 限制返回结果数量
            return results[:max_results] if results else []
                
        except Exception as e:
            self.logger.error(f"RAG检索错误: {e}")
            return []
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """搜索接口的别名"""
        return self.retrieve(query, max_results)
    
    def execute(self, query: str) -> List[Dict]:
        """
        兼容 RAGRetriever 接口的方法
        与 retrieve 相同，但不限制返回结果数量，保持与原 RAGRetriever 的兼容性
        """
        try:
            payload = {"question": query}
            response = requests.post(self.base_url, json=payload, timeout=self.timeout, 
                                  headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            result_data = response.json()
            
            if isinstance(result_data, dict) and 'results' in result_data:
                return result_data['results']
            if isinstance(result_data, list):
                return result_data
            return [{'content': str(result_data), 'source': 'RAG检索'}]
        except (requests.exceptions.RequestException, Exception):
            return [] 