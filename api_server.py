#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gauz文档Agent - FastAPI服务器
将多Agent文档生成系统封装为RESTful API服务

提供的接口：
- POST /generate_document - 生成文档
- GET /health - 健康检查
- GET /status - 系统状态
- POST /set_concurrency - 设置并发参数
- GET /download/{file_id} - 下载生成的文件
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
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 导入主要组件
try:
    from main import DocumentGenerationPipeline
    from config.settings import setup_logging, get_config
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

# ===== 数据模型 =====

class DocumentGenerationRequest(BaseModel):
    """文档生成请求模型"""
    query: str = Field(..., description="文档生成需求描述", min_length=1, max_length=2000)
    output_dir: Optional[str] = Field("outputs", description="输出目录名称")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "为城市更新项目编写环境影响评估报告",
                "output_dir": "outputs"
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
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DocumentGenerationResponse(BaseModel):
    """文档生成响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    files: Optional[Dict[str, str]] = Field(None, description="生成的文件")

class SystemStatus(BaseModel):
    """系统状态模型"""
    service: str
    status: str
    version: str
    active_tasks: int
    total_tasks: int
    concurrency_settings: Dict[str, Any]
    uptime: str

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

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    active_tasks = sum(1 for task in generation_tasks.values() 
                      if task["status"] in ["pending", "running"])
    
    # 计算运行时间（简化版本）
    uptime = "运行中"
    
    return SystemStatus(
        service="Gauz文档Agent API",
        status="running",
        version="1.0.0",
        active_tasks=active_tasks,
        total_tasks=len(generation_tasks),
        concurrency_settings=pipeline.get_concurrency_settings(),
        uptime=uptime
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
        # 更新状态为运行中
        task_info["status"] = "running"
        task_info["progress"] = "正在生成文档结构..."
        task_info["updated_at"] = datetime.now()
        
        logger.info(f"🚀 开始执行文档生成任务: {task_id}")
        
        # 创建任务专用输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"api_outputs/{task_id}_{timestamp}"
        
        # 在新的线程中运行同步代码
        loop = asyncio.get_event_loop()
        result_files = await loop.run_in_executor(
            None, 
            pipeline.generate_document, 
            request.query, 
            output_dir
        )
        
        # 生成文件下载链接
        file_links = {}
        for file_type, file_path in result_files.items():
            if file_type != 'output_directory' and os.path.exists(file_path):
                file_id = str(uuid.uuid4())
                file_storage[file_id] = file_path
                file_links[file_type] = f"/download/{file_id}"
        
        # 更新任务状态为完成
        task_info["status"] = "completed"
        task_info["progress"] = "文档生成完成"
        task_info["result"] = {
            "files": file_links,
            "output_directory": result_files.get("output_directory"),
            "generation_time": datetime.now().isoformat()
        }
        task_info["updated_at"] = datetime.now()
        
        logger.info(f"✅ 文档生成任务完成: {task_id}")
        
    except Exception as e:
        # 更新任务状态为失败
        task_info["status"] = "failed"
        task_info["progress"] = f"生成失败: {str(e)}"
        task_info["error"] = str(e)
        task_info["updated_at"] = datetime.now()
        
        logger.error(f"❌ 文档生成任务失败: {task_id} - {e}")

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
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")
    
    args = parser.parse_args()
    start_server(args.host, args.port, args.reload) 