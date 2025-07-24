#!/usr/bin/env python3
"""
外部API客户端

调用远程API服务，提供模板搜索和文档搜索功能
"""

import json
import time
import logging
import sys
import os
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

@dataclass
class TemplateSearchRequest:
    """模板搜索请求"""
    query: str

@dataclass 
class DocumentSearchRequest:
    """文档搜索请求"""
    query_text: str
    project_name: str = "default"
    top_k: int = 5
    content_type: str = "all"

class ExternalAPIClient:
    """外部API客户端"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # API服务器配置
        self.api_base_url = os.getenv("API_BASE_URL", "http://5bd116fe.r12.cpolar.top")
        self.timeout = int(os.getenv("API_TIMEOUT", "30"))
        self.skip_health_check = os.getenv("SKIP_HEALTH_CHECK", "false").lower() == "true"
        
        # 服务可用性标记
        self.template_available = False
        self.document_available = False
        
        # 初始化并检查服务状态
        if self.skip_health_check:
            self.template_available = True
            self.document_available = True
            self.logger.info("🔄 已跳过健康检查，假设所有服务可用")
        else:
            self._check_service_availability()
        
        self.logger.info(f"ExternalAPIClient 初始化完成，API服务器: {self.api_base_url}")
        self.logger.info(f"模板搜索服务: {'可用' if self.template_available else '不可用'}")
        self.logger.info(f"文档搜索服务: {'可用' if self.document_available else '不可用'}")
    
    def _check_service_availability(self):
        """检查服务可用性"""
        try:
            # 同步方式检查服务状态
            import requests
            
            # 优先尝试健康检查端点
            try:
                response = requests.get(f"{self.api_base_url}/health", timeout=5)
                if response.status_code == 200:
                    self.template_available = True
                    self.document_available = True
                    self.logger.info("✅ API服务健康检查成功")
                    return
                else:
                    self.logger.warning(f"⚠️ 健康检查响应异常: {response.status_code}")
            except Exception as e:
                self.logger.warning(f"⚠️ 健康检查失败: {e}")
            
            # 如果健康检查失败，尝试直接检查API端点可用性
            try:
                # 发送一个简单的OPTIONS请求检查服务器是否响应
                response = requests.options(f"{self.api_base_url}/template_search", timeout=5)
                # 只要服务器有响应就认为可用（包括405 Method Not Allowed等）
                if response.status_code in [200, 405, 404]:
                    self.template_available = True
                    self.logger.info("✅ 模板搜索端点可达")
            except Exception as e:
                self.logger.warning(f"⚠️ 模板搜索端点检查失败: {e}")
                # 即使检查失败，也假设服务可用，在实际调用时再处理错误
                self.template_available = True
                self.logger.info("🔄 假设模板搜索服务可用，将在调用时验证")
            
            try:
                # 检查文档搜索端点
                response = requests.options(f"{self.api_base_url}/document_search", timeout=5)
                if response.status_code in [200, 405, 404]:
                    self.document_available = True
                    self.logger.info("✅ 文档搜索端点可达")
            except Exception as e:
                self.logger.warning(f"⚠️ 文档搜索端点检查失败: {e}")
                # 即使检查失败，也假设服务可用
                self.document_available = True
                self.logger.info("🔄 假设文档搜索服务可用，将在调用时验证")
                
        except ImportError:
            self.logger.error("❌ 缺少requests库，无法检查服务状态")
            # 如果没有requests库，直接假设服务可用
            self.template_available = True
            self.document_available = True
            self.logger.info("🔄 跳过服务检查，假设服务可用")
    
    async def _make_api_request(self, endpoint: str, data: dict, max_retries: int = 3) -> Optional[dict]:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            max_retries: 最大重试次数
            
        Returns:
            Optional[dict]: API响应，失败时返回None
        """
        url = f"{self.api_base_url}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            self.logger.error(f"❌ API请求失败 (状态码: {response.status}): {error_text}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(1 * (attempt + 1))  # 指数退避
                            continue
                            
            except asyncio.TimeoutError:
                self.logger.error(f"❌ API请求超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
            except Exception as e:
                self.logger.error(f"❌ API请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
        
        return None
    
    def check_service_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """检查服务状态"""
        if force_refresh:
            self._check_service_availability()
            
        return {
            "service": "外部API客户端",
            "status": "running" if (self.template_available or self.document_available) else "degraded",
            "version": "3.0.0-api",
            "api_base_url": self.api_base_url,
            "tools": {
                "template_search": {
                    "available": self.template_available,
                    "endpoint": "/template_search"
                },
                "document_search": {
                    "available": self.document_available,
                    "endpoint": "/document_search"
                }
            },
            "mode": "api_client"
        }
    
    def template_search(self, query: str, max_retries: int = 3) -> Optional[str]:
        """
        模板搜索
        
        Args:
            query: 搜索查询
            max_retries: 最大重试次数
            
        Returns:
            Optional[str]: 模板内容，失败时返回None
        """
        if not self.template_available:
            self.logger.error("❌ 模板搜索服务不可用")
            return None
        
        # 使用同步方式调用异步函数
        return asyncio.run(self._template_search_async(query, max_retries))
    
    async def _template_search_async(self, query: str, max_retries: int = 3) -> Optional[str]:
        """异步模板搜索"""
        try:
            self.logger.info(f"🔍 API模板搜索: {query}")
            start_time = time.time()
            
            # 构造请求数据
            request_data = {"query": query}
            
            # 调用API
            response = await self._make_api_request("/template_search", request_data, max_retries)
            
            if response is None:
                self.logger.error("❌ 模板搜索API调用失败")
                return None
            
            # 提取模板内容
            template_content = response.get("template_content", "")
            
            response_time = time.time() - start_time
            self.logger.info(f"✅ 模板搜索成功: 耗时 {response_time:.2f}s, 内容长度 {len(template_content)} 字符")
            
            return template_content
            
        except Exception as e:
            self.logger.error(f"❌ 模板搜索失败: {e}")
            return None
    
    def document_search(self, query_text: str, project_name: str = "医灵古庙", 
                       top_k: int = 5, content_type: str = "all", 
                       max_retries: int = 3) -> Optional[Dict[str, List]]:
        """
        文档搜索
        
        Args:
            query_text: 搜索查询
            project_name: 项目名称
            top_k: 返回结果数量
            content_type: 内容类型
            max_retries: 最大重试次数
            
        Returns:
            Optional[Dict[str, List]]: 搜索结果，失败时返回None
        """
        if not self.document_available:
            self.logger.error("❌ 文档搜索服务不可用")
            return None
        
        # 使用同步方式调用异步函数
        return asyncio.run(self._document_search_async(query_text, project_name, top_k, content_type, max_retries))
    
    async def _document_search_async(self, query_text: str, project_name: str = "医灵古庙", 
                                   top_k: int = 5, content_type: str = "all", 
                                   max_retries: int = 3) -> Optional[Dict[str, List]]:
        """异步文档搜索"""
        try:
            self.logger.info(f"📄 API文档搜索: {query_text} (项目: {project_name}, top_k: {top_k})")
            start_time = time.time()
            
            # 构造请求数据
            request_data = {
                "query_text": query_text,
                "project_name": project_name,
                "top_k": top_k,
                "content_type": content_type
            }
            
            # 调用API
            response = await self._make_api_request("/document_search", request_data, max_retries)
            
            if response is None:
                self.logger.error("❌ 文档搜索API调用失败")
                return None
            
            # 提取搜索结果
            retrieved_text = response.get('retrieved_text', [])
            retrieved_image = response.get('retrieved_image', [])
            retrieved_table = response.get('retrieved_table', [])
            
            response_time = time.time() - start_time
            total_results = len(retrieved_text) + len(retrieved_image) + len(retrieved_table)
            
            self.logger.info(f"✅ 文档搜索成功: 耗时 {response_time:.2f}s, 结果 {total_results} 条 "
                           f"(文本:{len(retrieved_text)}, 图片:{len(retrieved_image)}, 表格:{len(retrieved_table)})")
            
            return {
                'retrieved_text': retrieved_text,
                'retrieved_image': retrieved_image,
                'retrieved_table': retrieved_table
            }
            
        except Exception as e:
            self.logger.error(f"❌ 文档搜索失败: {e}")
            return None
    
    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "active_requests": 0,  # API调用无本地并发统计
            "total_requests": 0,
            "available_template_tools": 1 if self.template_available else 0,
            "available_document_tools": 1 if self.document_available else 0,
            "mode": "api_client",
            "api_base_url": self.api_base_url
        }
    
    def close(self):
        """关闭客户端"""
        self.logger.info("ExternalAPIClient 关闭（API客户端无需特殊清理）")

# 单例模式的全局客户端实例
_global_external_client = None

def get_external_api_client() -> ExternalAPIClient:
    """获取全局外部API客户端实例"""
    global _global_external_client
    if _global_external_client is None:
        _global_external_client = ExternalAPIClient()
    return _global_external_client 