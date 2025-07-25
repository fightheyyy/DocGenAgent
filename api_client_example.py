#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gauz文档Agent API 客户端使用示例

演示如何通过HTTP API调用文档生成服务
"""

import requests
import time
import json
from typing import Dict, Any

class GauzDocumentAPI:
    """Gauz文档Agent API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        response = requests.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()
    
    def set_concurrency(self, orchestrator_workers: int = None, 
                       react_workers: int = None, content_workers: int = None,
                       rate_delay: float = None) -> Dict[str, Any]:
        """设置并发参数"""
        data = {}
        if orchestrator_workers is not None:
            data["orchestrator_workers"] = orchestrator_workers
        if react_workers is not None:
            data["react_workers"] = react_workers
        if content_workers is not None:
            data["content_workers"] = content_workers
        if rate_delay is not None:
            data["rate_delay"] = rate_delay
            
        response = requests.post(f"{self.base_url}/set_concurrency", json=data)
        response.raise_for_status()
        return response.json()
    
    def generate_document(self, query: str, output_dir: str = "outputs") -> str:
        """
        生成文档
        
        Returns:
            str: 任务ID
        """
        data = {
            "query": query,
            "output_dir": output_dir
        }
        
        response = requests.post(f"{self.base_url}/generate_document", json=data)
        response.raise_for_status()
        result = response.json()
        return result["task_id"]
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        response = requests.get(f"{self.base_url}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, task_id: str, timeout: int = 1800, 
                           check_interval: int = 10) -> Dict[str, Any]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间(秒)
            check_interval: 检查间隔(秒)
            
        Returns:
            Dict: 任务完成状态
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            
            print(f"📊 任务状态: {status['status']} - {status['progress']}")
            
            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                raise Exception(f"任务失败: {status.get('error', '未知错误')}")
            
            time.sleep(check_interval)
        
        raise TimeoutError(f"任务超时 ({timeout}秒)")
    
    def download_file(self, file_id: str, save_path: str):
        """下载文件"""
        response = requests.get(f"{self.base_url}/download/{file_id}")
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
    
    def list_tasks(self, limit: int = 20, status_filter: str = None) -> Dict[str, Any]:
        """获取任务列表"""
        params = {"limit": limit}
        if status_filter:
            params["status_filter"] = status_filter
            
        response = requests.get(f"{self.base_url}/tasks", params=params)
        response.raise_for_status()
        return response.json()

def example_usage():
    """使用示例"""
    print("🚀 Gauz文档Agent API 使用示例")
    print("=" * 60)
    
    # 初始化客户端
    client = GauzDocumentAPI("http://localhost:8000")
    
    try:
        # 1. 健康检查
        print("1️⃣ 健康检查...")
        health = client.health_check()
        print(f"   ✅ 服务状态: {health['status']}")
        
        # 2. 获取系统状态
        print("\n2️⃣ 获取系统状态...")
        status = client.get_system_status()
        print(f"   📊 活跃任务: {status['active_tasks']}")
        print(f"   📈 总任务数: {status['total_tasks']}")
        
        # 3. 设置并发参数（可选）
        print("\n3️⃣ 设置并发参数...")
        concurrency_result = client.set_concurrency(
            orchestrator_workers=3,
            react_workers=5,
            content_workers=4,
            rate_delay=1.0
        )
        print(f"   ✅ {concurrency_result['message']}")
        
        # 4. 生成文档
        print("\n4️⃣ 开始生成文档...")
        query = "为新能源汽车充电站项目编写可行性研究报告"
        task_id = client.generate_document(query)
        print(f"   📝 任务已提交，任务ID: {task_id}")
        
        # 5. 等待完成
        print("\n5️⃣ 等待文档生成完成...")
        final_status = client.wait_for_completion(task_id, timeout=1800)
        
        # 6. 获取结果
        print("\n6️⃣ 文档生成完成！")
        if final_status.get("result") and final_status["result"].get("files"):
            files = final_status["result"]["files"]
            print("   📄 生成的文件:")
            for file_type, download_url in files.items():
                print(f"      {file_type}: {download_url}")
                
                # 可以下载文件（示例）
                # file_id = download_url.split('/')[-1]
                # client.download_file(file_id, f"{file_type}.json")
        
        print(f"\n🎉 示例执行完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("💡 请确保API服务器正在运行: python start_api.py")
    except Exception as e:
        print(f"❌ 执行失败: {e}")

if __name__ == "__main__":
    example_usage() 