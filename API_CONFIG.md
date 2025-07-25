# API 配置说明

## 环境变量配置

### 模板搜索服务
- **TEMPLATE_API_URL**: 模板搜索API服务器地址
  - 默认值: `http://5bd116fe.r12.cpolar.top`
  - 端点: `/template_search`

### RAG检索服务  
- **RAG_API_URL**: RAG检索API服务器地址
  - 默认值: `http://localhost:8000`
  - 端点: `/api/v1/search`

### 通用配置
- **API_TIMEOUT**: API请求超时时间(秒)
  - 默认值: `30`
- **SKIP_HEALTH_CHECK**: 跳过健康检查
  - 默认值: `false`

## 服务架构

```
Gauz文档Agent
├── 模板搜索服务 (外部)
│   ├── URL: TEMPLATE_API_URL
│   ├── 端点: /template_search
│   └── 功能: 搜索文档模板
└── RAG检索服务 (本地)
    ├── URL: RAG_API_URL
    ├── 端点: /api/v1/search
    └── 功能: 项目级别智能检索
```

## API接口格式

### 模板搜索
**请求:**
```json
POST {TEMPLATE_API_URL}/template_search
{
  "query": "搜索关键词"
}
```

**响应:**
```json
{
  "template_content": "模板内容..."
}
```

### RAG检索
**请求:**
```json
POST {RAG_API_URL}/api/v1/search
{
  "query": "搜索查询",
  "project_name": "项目名称",
  "search_type": "hybrid",
  "top_k": 5
}
```

**响应:**
```json
{
  "status": "success",
  "message": "搜索完成",
  "data": {
    "retrieved_text": "检索到的文本内容...",
    "retrieved_images": [
      "http://example.com/image1.jpg",
      "http://example.com/image2.jpg"
    ],
    "metadata": {
      "total_pages": 5,
      "search_type": "hybrid",
      "scores": [0.8, 0.7, 0.6],
      "page_numbers": [1, 2, 3],
      "project_name": "项目名称"
    }
  },
  "error": null
}
```

## 配置示例

### 环境变量设置
```bash
# Windows
set TEMPLATE_API_URL=http://your-template-server.com
set RAG_API_URL=http://localhost:8000
set API_TIMEOUT=60
set SKIP_HEALTH_CHECK=true

# Linux/Mac
export TEMPLATE_API_URL=http://your-template-server.com
export RAG_API_URL=http://localhost:8000
export API_TIMEOUT=60
export SKIP_HEALTH_CHECK=true
```

### Python代码配置
```python
import os
from clients.external_api_client import ExternalAPIClient

# 设置环境变量
os.environ['TEMPLATE_API_URL'] = 'http://your-template-server.com'
os.environ['RAG_API_URL'] = 'http://localhost:8000'

# 初始化客户端
client = ExternalAPIClient()
```

## 服务部署

### RAG检索服务 (localhost:8000)
1. 确保RAG检索服务在localhost:8000运行
2. 验证 `/api/v1/search` 端点可用
3. 确保项目数据已建立索引

### 模板搜索服务 (外部)
1. 确保模板搜索服务正常运行
2. 验证 `/template_search` 端点可用
3. 确保网络连通性

## 故障排除

### 常见问题

1. **RAG检索服务连接失败**
   ```
   ❌ RAG检索服务检查失败: Connection refused
   ```
   - 检查localhost:8000是否有服务运行
   - 确认 `/api/v1/search` 端点存在

2. **模板搜索服务连接失败**
   ```
   ❌ 模板搜索服务检查失败: Name resolution failed
   ```
   - 检查 TEMPLATE_API_URL 是否正确
   - 确认网络连通性

3. **项目未找到错误**
   ```
   项目 'project_name' 未找到，请先创建embedding索引
   ```
   - 确认项目名称正确
   - 检查项目数据是否已建立索引

### 调试建议

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **测试服务连通性**
   ```python
   from clients.external_api_client import ExternalAPIClient
   client = ExternalAPIClient()
   status = client.check_service_status()
   print(status)
   ```

3. **跳过健康检查**
   ```bash
   export SKIP_HEALTH_CHECK=true
   ``` 