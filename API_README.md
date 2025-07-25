# Gauz文档Agent API 使用指南

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动API服务器
```bash
# 方式1：使用快速启动脚本
python start_api.py

# 方式2：使用完整参数
python api_server.py --host 0.0.0.0 --port 8000

# 方式3：开发模式（自动重载）
python api_server.py --reload
```

### 3. 访问API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 📋 API接口列表

### 基础接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/status` | 获取系统状态 |
| POST | `/set_concurrency` | 设置并发参数 |

### 文档生成接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/generate_document` | 提交文档生成任务 |
| GET | `/tasks/{task_id}` | 获取任务状态 |
| GET | `/tasks` | 获取任务列表 |
| GET | `/download/{file_id}` | 下载生成的文件 |

## 🔧 使用示例

### Python客户端示例

```python
import requests
import time

# 1. 健康检查
response = requests.get("http://localhost:8000/health")
print(response.json())

# 2. 提交文档生成任务
task_data = {
    "query": "为城市更新项目编写环境影响评估报告",
    "output_dir": "outputs"
}
response = requests.post("http://localhost:8000/generate_document", json=task_data)
task_id = response.json()["task_id"]
print(f"任务ID: {task_id}")

# 3. 轮询任务状态
while True:
    response = requests.get(f"http://localhost:8000/tasks/{task_id}")
    status = response.json()
    print(f"状态: {status['status']} - {status['progress']}")
    
    if status["status"] == "completed":
        print("文档生成完成！")
        if status.get("result") and status["result"].get("files"):
            for file_type, download_url in status["result"]["files"].items():
                print(f"{file_type}: {download_url}")
        break
    elif status["status"] == "failed":
        print(f"生成失败: {status.get('error')}")
        break
    
    time.sleep(10)  # 等待10秒后再次检查
```

### curl 示例

```bash
# 健康检查
curl http://localhost:8000/health

# 提交文档生成任务
curl -X POST "http://localhost:8000/generate_document" \
     -H "Content-Type: application/json" \
     -d '{"query": "为智慧城市项目编写技术方案书", "output_dir": "outputs"}'

# 查询任务状态
curl http://localhost:8000/tasks/{task_id}

# 下载文件
curl -O http://localhost:8000/download/{file_id}
```

## 📊 请求响应格式

### 文档生成请求
```json
{
  "query": "文档生成需求描述",
  "output_dir": "outputs"
}
```

### 文档生成响应
```json
{
  "task_id": "uuid-string",
  "status": "pending",
  "message": "文档生成任务已提交，任务ID: uuid-string",
  "files": null
}
```

### 任务状态响应
```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "progress": "文档生成完成",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:30:00",
  "result": {
    "files": {
      "document_guide": "/download/file-id-1",
      "enriched_guide": "/download/file-id-2",
      "final_document": "/download/file-id-3"
    },
    "output_directory": "api_outputs/task_id_timestamp",
    "generation_time": "2024-01-01T12:30:00"
  },
  "error": null
}
```

## ⚙️ 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `API_BASE_URL` | `http://5bd116fe.r12.cpolar.top` | 外部API服务器地址 |
| `API_TIMEOUT` | `30` | API请求超时时间(秒) |
| `SKIP_HEALTH_CHECK` | `false` | 跳过健康检查 |

### 并发参数设置

```python
# 设置并发参数
concurrency_data = {
    "orchestrator_workers": 3,    # 编排代理线程数
    "react_workers": 5,           # 检索代理线程数  
    "content_workers": 4,         # 内容生成代理线程数
    "rate_delay": 1.0            # 请求间隔时间(秒)
}

response = requests.post("http://localhost:8000/set_concurrency", 
                        json=concurrency_data)
```

## 📁 文件结构

生成的文档包含以下文件：

1. **document_guide**: 文档结构和写作指导
2. **enriched_guide**: 包含检索资料的增强指导
3. **generation_input**: 内容生成器的输入文件
4. **final_document**: 最终生成的完整文档

## 🔍 任务状态说明

| 状态 | 说明 |
|------|------|
| `pending` | 任务已提交，等待处理 |
| `running` | 任务正在执行中 |
| `completed` | 任务成功完成 |
| `failed` | 任务执行失败 |
| `cancelled` | 任务被取消 |

## 🚨 错误处理

### 常见错误码

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 请求成功 |
| 404 | 资源不存在（任务ID或文件ID无效） |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用（系统未初始化） |

### 错误响应格式
```json
{
  "detail": "错误详细信息"
}
```

## 🛠️ 开发调试

### 启用开发模式
```bash
python api_server.py --reload
```

### 查看日志
API服务器会输出详细的日志信息，包括：
- 任务提交和执行状态
- 文档生成各阶段进度
- 错误信息和调试信息

### 运行客户端示例
```bash
python api_client_example.py
```

## 📝 注意事项

1. **文档生成时间**: 根据需求复杂度，生成时间可能在几分钟到几十分钟不等
2. **并发限制**: 建议根据服务器资源调整并发参数
3. **文件清理**: 生成的文件会保存在 `api_outputs` 目录中，需要定期清理
4. **超时设置**: 复杂文档生成可能需要较长时间，建议设置合适的超时时间

## 🔗 相关链接

- [主程序使用说明](README.md)
- [API接口文档](http://localhost:8000/docs)
- [项目源码](./) 