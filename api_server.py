#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gauz文档Agent - FastAPI服务器
将多Agent文档生成系统封装为RESTful API服务

提供的接口：
- POST /generate_document - 生成文档（自动管理输出目录）
- GET /health - 健康检查
- GET /status - 系统状态
- POST /set_concurrency - 设置并发参数
- GET /download/{file_id} - 下载生成的文件（备用）
- MinIO自动上传 - 主要文件分发方式
"""

import sys
import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# 必须在所有其他导入之前禁用ChromaDB telemetry
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'True'

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json

# 导入主要组件
try:
    from main import DocumentGenerationPipeline
    from config.settings import setup_logging, get_config
    from config.minio_config import get_minio_client, upload_document_files
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Gauz文档Agent API",
    description="基于多Agent架构的智能长文档生成系统API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
pipeline: Optional[DocumentGenerationPipeline] = None
generation_tasks: Dict[str, Dict[str, Any]] = {}  # 存储任务状态
file_storage: Dict[str, str] = {}  # 存储文件映射

# ===== 日志管理器 =====

class LogManager:
    """任务日志管理器"""
    def __init__(self):
        self.task_logs: Dict[str, List[Dict[str, Any]]] = {}  # 存储任务日志
        self.log_subscribers: Dict[str, List[asyncio.Queue]] = {}  # 存储日志订阅者
        self.max_logs_per_task = 1000  # 每个任务最多保存的日志数量
        
    def add_log(self, task_id: str, log_entry: Dict[str, Any]):
        """添加日志条目"""
        if task_id not in self.task_logs:
            self.task_logs[task_id] = []
        
        # 添加时间戳（如果没有的话）
        if 'timestamp' not in log_entry:
            log_entry['timestamp'] = datetime.now().isoformat()
            
        self.task_logs[task_id].append(log_entry)
        
        # 限制日志数量，避免内存溢出
        if len(self.task_logs[task_id]) > self.max_logs_per_task:
            self.task_logs[task_id] = self.task_logs[task_id][-self.max_logs_per_task:]
        
        # 推送给所有订阅者
        self._notify_subscribers(task_id, log_entry)
        
        # 同时记录到系统日志
        log_level = log_entry.get('type', 'info')
        message = f"[{task_id}] {log_entry.get('message', '')}"
        if log_level == 'error':
            logger.error(message)
        elif log_level == 'warning':
            logger.warning(message)
        else:
            logger.info(message)
    
    def _notify_subscribers(self, task_id: str, log_entry: Dict[str, Any]):
        """通知订阅者"""
        if task_id in self.log_subscribers:
            # 创建队列副本以避免迭代时修改
            subscribers = self.log_subscribers[task_id].copy()
            for queue in subscribers:
                try:
                    queue.put_nowait(log_entry)
                except asyncio.QueueFull:
                    # 队列满了，移除这个订阅者
                    try:
                        self.log_subscribers[task_id].remove(queue)
                    except ValueError:
                        pass  # 队列已经被移除
    
    async def subscribe_logs(self, task_id: str) -> asyncio.Queue:
        """订阅任务日志"""
        queue = asyncio.Queue(maxsize=100)
        if task_id not in self.log_subscribers:
            self.log_subscribers[task_id] = []
        self.log_subscribers[task_id].append(queue)
        return queue
    
    def unsubscribe_logs(self, task_id: str, queue: asyncio.Queue):
        """取消订阅任务日志"""
        if task_id in self.log_subscribers:
            try:
                self.log_subscribers[task_id].remove(queue)
                if not self.log_subscribers[task_id]:  # 如果没有订阅者了
                    del self.log_subscribers[task_id]
            except ValueError:
                pass  # 队列不在列表中
    
    def get_logs(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有日志"""
        return self.task_logs.get(task_id, [])
    
    def cleanup_task_logs(self, task_id: str):
        """清理任务日志（任务完成后调用）"""
        # 保留日志1小时，然后清理
        if task_id in self.task_logs:
            # 这里可以实现延时清理，暂时保留
            pass
        
        # 立即清理订阅者
        if task_id in self.log_subscribers:
            del self.log_subscribers[task_id]

# 创建全局日志管理器
log_manager = LogManager()

# ===== 数据模型 =====

class DocumentGenerationRequest(BaseModel):
    """文档生成请求模型"""
    query: str = Field(..., description="文档生成需求描述", min_length=1, max_length=2000)
    project_name: str = Field(..., description="项目名称，用于RAG检索", min_length=1, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "我想生成一个关于医灵古庙的文物影响评估报告",
                "project_name": "医灵古庙"
            }
        }

class ConcurrencySettings(BaseModel):
    """并发设置模型"""
    orchestrator_workers: Optional[int] = Field(None, ge=1, le=10, description="编排代理线程数")
    react_workers: Optional[int] = Field(None, ge=1, le=10, description="检索代理线程数")
    content_workers: Optional[int] = Field(None, ge=1, le=10, description="内容生成代理线程数")
    rate_delay: Optional[float] = Field(None, ge=0.1, le=10.0, description="请求间隔时间(秒)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "orchestrator_workers": 3,
                "react_workers": 5,
                "content_workers": 4,
                "rate_delay": 1.0
            }
        }

class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: str
    created_at: datetime
    updated_at: datetime
    request: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DocumentGenerationResponse(BaseModel):
    """文档生成响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    files: Optional[Dict[str, str]] = Field(None, description="生成的文件（本地下载链接）")
    minio_urls: Optional[Dict[str, str]] = Field(None, description="MinIO存储的文件下载链接")

class SystemStatus(BaseModel):
    """系统状态模型"""
    service: str
    status: str
    version: str
    active_tasks: int
    total_tasks: int
    concurrency_settings: Dict[str, Any]
    uptime: str
    minio_status: str = Field(..., description="MinIO存储服务状态")

# ===== 初始化函数 =====

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global pipeline
    try:
        logger.info("🚀 正在启动Gauz文档Agent API服务...")
        pipeline = DocumentGenerationPipeline()
        logger.info("✅ 文档生成流水线初始化成功")
        
        # 创建输出目录
        os.makedirs("outputs", exist_ok=True)
        os.makedirs("api_outputs", exist_ok=True)
        
        # 初始化MinIO客户端
        minio_client = get_minio_client()
        if minio_client.is_available():
            logger.info("✅ MinIO客户端连接成功")
        else:
            logger.warning("⚠️ MinIO客户端连接失败，将使用本地文件存储")
        
        logger.info("🌟 Gauz文档Agent API服务启动完成！")
        
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    logger.info("🔄 正在关闭Gauz文档Agent API服务...")
    
    # 清理未完成的任务
    for task_id, task_info in generation_tasks.items():
        if task_info["status"] in ["pending", "running"]:
            task_info["status"] = "cancelled"
            task_info["updated_at"] = datetime.now()
    
    logger.info("✅ 服务关闭完成")

# ===== 核心API接口 =====

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "Gauz文档Agent API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/logs/{task_id}/stream")
async def stream_task_logs(task_id: str):
    """实时推送任务日志流（Server-Sent Events）"""
    
    # 检查任务是否存在
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    async def log_generator():
        """日志生成器"""
        log_queue = None
        try:
            # 订阅日志
            log_queue = await log_manager.subscribe_logs(task_id)
            
            # 首先发送历史日志
            historical_logs = log_manager.get_logs(task_id)
            for log_entry in historical_logs:
                data = json.dumps(log_entry, ensure_ascii=False)
                yield f"data: {data}\n\n"
            
            # 发送当前任务状态
            task_status_log = {
                "timestamp": datetime.now().isoformat(),
                "type": "status",
                "message": f"当前任务状态: {generation_tasks[task_id]['status']}",
                "task_status": generation_tasks[task_id]['status'],
                "progress": generation_tasks[task_id].get('progress', ''),
            }
            data = json.dumps(task_status_log, ensure_ascii=False)
            yield f"data: {data}\n\n"
            
            # 实时推送新日志
            while True:
                try:
                    # 等待新的日志条目，设置超时防止连接挂起
                    log_entry = await asyncio.wait_for(log_queue.get(), timeout=30.0)
                    data = json.dumps(log_entry, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                    
                    # 如果任务已完成或失败，发送结束信号
                    if log_entry.get('type') in ['success', 'error'] or log_entry.get('step') == '任务完成':
                        # 等待一小段时间再结束连接
                        await asyncio.sleep(1)
                        end_log = {
                            "timestamp": datetime.now().isoformat(),
                            "type": "stream_end",
                            "message": "日志流结束"
                        }
                        data = json.dumps(end_log, ensure_ascii=False)
                        yield f"data: {data}\n\n"
                        break
                        
                except asyncio.TimeoutError:
                    # 发送心跳，保持连接活跃
                    heartbeat = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "heartbeat",
                        "message": "连接正常"
                    }
                    data = json.dumps(heartbeat, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                    
        except Exception as e:
            # 发送错误信息
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "type": "stream_error",
                "message": f"日志流异常: {str(e)}"
            }
            data = json.dumps(error_log, ensure_ascii=False)
            yield f"data: {data}\n\n"
            
        finally:
            # 清理订阅
            if log_queue:
                log_manager.unsubscribe_logs(task_id, log_queue)
    
    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )

@app.get("/logs/{task_id}")
async def get_task_logs(task_id: str):
    """获取任务的历史日志"""
    
    # 检查任务是否存在
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    logs = log_manager.get_logs(task_id)
    
    return {
        "task_id": task_id,
        "task_status": generation_tasks[task_id]["status"],
        "log_count": len(logs),
        "logs": logs,
        "last_updated": generation_tasks[task_id]["updated_at"].isoformat()
    }

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    active_tasks = sum(1 for task in generation_tasks.values() 
                      if task["status"] in ["pending", "running"])
    
    # 计算运行时间（简化版本）
    uptime = "运行中"
    
    # 检查MinIO状态
    minio_client = get_minio_client()
    minio_status = "available" if minio_client.is_available() else "unavailable"
    
    return SystemStatus(
        service="Gauz文档Agent API",
        status="running",
        version="1.0.0",
        active_tasks=active_tasks,
        total_tasks=len(generation_tasks),
        concurrency_settings=pipeline.get_concurrency_settings(),
        uptime=uptime,
        minio_status=minio_status
    )

@app.post("/set_concurrency")
async def set_concurrency(settings: ConcurrencySettings):
    """设置并发参数"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        pipeline.set_concurrency(
            orchestrator_workers=settings.orchestrator_workers,
            react_workers=settings.react_workers,
            content_workers=settings.content_workers,
            rate_delay=settings.rate_delay
        )
        
        logger.info(f"✅ 并发设置已更新: {settings.dict()}")
        
        return {
            "status": "success",
            "message": "并发设置已更新",
            "current_settings": pipeline.get_concurrency_settings()
        }
        
    except Exception as e:
        logger.error(f"❌ 设置并发参数失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")

@app.post("/generate_document", response_model=DocumentGenerationResponse)
async def generate_document(request: DocumentGenerationRequest, background_tasks: BackgroundTasks):
    """
    生成文档接口 - 异步处理
    
    提交文档生成任务，返回任务ID。可通过任务ID查询进度和下载结果。
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task_info = {
        "task_id": task_id,
        "status": "pending",
        "progress": "任务已提交，等待处理",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "request": request.dict(),
        "result": None,
        "error": None
    }
    
    generation_tasks[task_id] = task_info
    
    # 添加后台任务
    background_tasks.add_task(run_document_generation, task_id, request)
    
    logger.info(f"📝 新的文档生成任务: {task_id} - {request.query}")
    
    return DocumentGenerationResponse(
        task_id=task_id,
        status="pending",
        message=f"文档生成任务已提交，任务ID: {task_id}",
        files=None
    )

@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_info = generation_tasks[task_id]
    
    return TaskStatus(
        task_id=task_info["task_id"],
        status=task_info["status"],
        progress=task_info["progress"],
        created_at=task_info["created_at"],
        updated_at=task_info["updated_at"],
        request=task_info.get("request"),
        result=task_info["result"],
        error=task_info["error"]
    )

@app.get("/tasks")
async def list_tasks(limit: int = 20, status_filter: Optional[str] = None):
    """获取任务列表"""
    tasks = list(generation_tasks.values())
    
    # 状态过滤
    if status_filter:
        tasks = [task for task in tasks if task["status"] == status_filter]
    
    # 按时间排序，最新的在前
    tasks.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 限制数量
    tasks = tasks[:limit]
    
    return {
        "total": len(generation_tasks),
        "filtered": len(tasks),
        "tasks": tasks
    }

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """下载生成的文件"""
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path = file_storage[file_id]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    filename = os.path.basename(file_path)
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

# ===== 后台任务函数 =====

async def run_document_generation(task_id: str, request: DocumentGenerationRequest):
    """后台执行文档生成任务"""
    task_info = generation_tasks[task_id]
    
    try:
        # 推送开始日志
        log_manager.add_log(task_id, {
            "type": "info",
            "message": "文档生成任务已启动",
            "progress": 0,
            "step": "任务初始化",
            "query": request.query,
            "project_name": request.project_name
        })
        
        # 更新状态为运行中
        task_info["status"] = "running"
        task_info["progress"] = "正在生成文档结构..."
        task_info["updated_at"] = datetime.now()
        
        # 推送状态更新
        log_manager.add_log(task_id, {
            "type": "progress",
            "message": "正在初始化文档生成流水线...",
            "progress": 5,
            "step": "流水线初始化"
        })
        
        logger.info(f"🚀 开始执行文档生成任务: {task_id}")
        
        # 创建任务专用输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"api_outputs/{task_id}_{timestamp}"
        
        # 推送目录创建日志
        log_manager.add_log(task_id, {
            "type": "progress",
            "message": f"创建输出目录: {output_dir}",
            "progress": 10,
            "step": "目录创建",
            "output_dir": output_dir
        })
        
        # 推送文档生成开始
        log_manager.add_log(task_id, {
            "type": "progress",
            "message": "开始执行多Agent文档生成流水线...",
            "progress": 15,
            "step": "多Agent协作"
        })
        
        # 在新的线程中运行同步代码
        loop = asyncio.get_event_loop()
        result_files = await loop.run_in_executor(
            None, 
            pipeline.generate_document, 
            request.query,
            request.project_name,
            output_dir
        )
        
        # 推送文档生成完成
        log_manager.add_log(task_id, {
            "type": "progress",
            "message": "文档内容生成完成，正在处理文件...",
            "progress": 70,
            "step": "文件处理",
            "generated_files": list(result_files.keys())
        })
        
        # 生成本地文件下载链接
        file_links = {}
        for file_type, file_path in result_files.items():
            if file_type != 'output_directory' and os.path.exists(file_path):
                file_id = str(uuid.uuid4())
                file_storage[file_id] = file_path
                file_links[file_type] = f"/download/{file_id}"
        
        # 上传文件到MinIO
        task_info["progress"] = "正在上传文件到MinIO..."
        task_info["updated_at"] = datetime.now()
        
        # 推送MinIO上传开始
        log_manager.add_log(task_id, {
            "type": "progress",
            "message": "开始上传文件到云存储(MinIO)...",
            "progress": 80,
            "step": "云存储上传"
        })
        
        minio_urls = {}
        try:
            logger.info(f"📤 开始上传文件到MinIO: {task_id}")
            minio_urls = upload_document_files(result_files, task_id)
            if minio_urls:
                logger.info(f"✅ MinIO上传成功: {len(minio_urls)} 个文件")
                log_manager.add_log(task_id, {
                    "type": "success",
                    "message": f"云存储上传成功，共上传 {len(minio_urls)} 个文件",
                    "progress": 90,
                    "step": "上传完成",
                    "minio_files": len(minio_urls)
                })
            else:
                logger.warning(f"⚠️ MinIO上传失败，仅提供本地下载")
                log_manager.add_log(task_id, {
                    "type": "warning",
                    "message": "云存储上传失败，仅提供本地下载",
                    "progress": 85,
                    "step": "上传失败"
                })
        except Exception as e:
            logger.error(f"❌ MinIO上传异常: {e}")
            log_manager.add_log(task_id, {
                "type": "error",
                "message": f"云存储上传异常: {str(e)}",
                "progress": 85,
                "step": "上传异常",
                "error": str(e)
            })
        
        # 更新任务状态为完成
        task_info["status"] = "completed"
        task_info["progress"] = "文档生成和上传完成"
        task_info["result"] = {
            "files": file_links,
            "minio_urls": minio_urls,
            "output_directory": result_files.get("output_directory"),
            "generation_time": datetime.now().isoformat(),
            "storage_info": {
                "local_files": len(file_links),
                "minio_files": len(minio_urls),
                "total_size_mb": sum(
                    os.path.getsize(file_path) / (1024 * 1024) 
                    for file_path in result_files.values() 
                    if file_path != result_files.get("output_directory") and os.path.exists(file_path)
                )
            }
        }
        task_info["updated_at"] = datetime.now()
        
        # 推送任务完成日志
        log_manager.add_log(task_id, {
            "type": "success",
            "message": "✅ 文档生成任务完成！",
            "progress": 100,
            "step": "任务完成",
            "result": {
                "minio_urls": minio_urls,
                "local_files": file_links,
                "storage_info": task_info["result"]["storage_info"]
            }
        })
        
        logger.info(f"✅ 文档生成任务完成: {task_id}")
        
    except Exception as e:
        # 推送错误日志
        log_manager.add_log(task_id, {
            "type": "error",
            "message": f"❌ 文档生成任务失败: {str(e)}",
            "progress": 0,
            "step": "任务失败",
            "error": str(e)
        })
        
        # 更新任务状态为失败
        task_info["status"] = "failed"
        task_info["progress"] = f"生成失败: {str(e)}"
        task_info["error"] = str(e)
        task_info["updated_at"] = datetime.now()
        
        logger.error(f"❌ 文档生成任务失败: {task_id} - {e}")
    finally:
        # 任务完成后清理日志订阅者（但保留日志1小时）
        log_manager.cleanup_task_logs(task_id)

# ===== 启动服务器 =====

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """启动FastAPI服务器"""
    print("🚀 启动Gauz文档Agent API服务器...")
    print(f"📊 服务地址: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print(f"📚 ReDoc文档: http://{host}:{port}/redoc")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gauz文档Agent API服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8002, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")
    
    args = parser.parse_args()
    start_server(args.host, args.port, args.reload) 