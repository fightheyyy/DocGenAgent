# ReactAgent - 智能文档生成系统

## 系统概述

ReactAgent是一个基于AI的智能文档生成系统，支持多种文档格式的自动生成，包括PDF解析、知识检索、模板填充和文档输出等核心功能。

## 🚀 快速开始

### 1. 环境要求

**Python版本要求：**
- **Python 3.12** （必需）
- ⚠️ **重要：必须使用Python 3.12，不能使用Python 3.13**
- 原因：camel-ai依赖限制最高支持Python 3.12

**推荐使用conda环境：**
```bash
# 创建新的conda环境
conda create -n gauz-agent-py312 python=3.12
conda activate gauz-agent-py312
```

### 2. 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt
```

**主要依赖说明：**
- `docling>=2.1.0` - 高级PDF解析
- `camel-ai>=0.1.7` - AI模型集成
- `chromadb>=0.4.18` - 向量数据库
- `minio>=7.2.0` - 云存储
- `colorama>=0.4.6` - 终端颜色支持

### 3. 环境配置

**创建环境变量文件：**
```bash
# 复制环境变量模板
cp .env.example .env
```

**必需的API密钥：**
```bash
# 编辑 .env 文件
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key-here
```

**API密钥获取方式：**
- **DeepSeek API**: 访问 [DeepSeek 官网](https://platform.deepseek.com/) 获取
- **OpenRouter API**: 访问 [OpenRouter 官网](https://openrouter.ai/) 获取

### 4. 配置前端（可选）

```bash
cp frontend/config.example.js frontend/config.js
```

### 5. 启动系统

```bash
# 启动Web服务
python scripts/web_app.py

# 或使用Agent
python scripts/run_agent.py --task "生成一份技术报告"
```

## 核心功能

### 1. 文档生成工具 (Document Generator)
- **长文档生成**：自动创建详细的长篇报告（支持章节化结构）
- **短文档生成**：快速生成精简的短篇报告
- **🆕 智能图片检索**：根据文档内容自动检索并插入相关图片
- **多格式输出**：支持Markdown和DOCX格式
- **云端同步**：自动上传到MinIO存储

### 2. RAG工具 (RAG Tool)
- **文档向量化**：将文档内容转换为向量进行存储
- **智能搜索**：基于语义相似度的内容检索
- **图片管理**：支持图片上传和基于内容的图片搜索
- **模板填充**：基于知识库自动填充模板字段

### 3. PDF解析工具 (PDF Parser)
- **智能解析**：提取PDF中的文本、图片和表格
- **结构化输出**：生成JSON格式的结构化内容
- **多媒体支持**：处理复杂的PDF格式和嵌入式内容

## 🆕 图片检索功能

### 功能特色
- **智能匹配**：根据章节标题和内容自动搜索相关图片
- **自动插入**：在适当位置插入相关图片到文档中
- **多格式支持**：
  - Markdown格式：`![描述](图片URL)`
  - DOCX格式：自动下载并嵌入图片
- **描述生成**：为每张图片生成详细的说明文字

### 工作原理
1. 在生成每个章节时，系统会自动搜索相关图片
2. 基于内容相关度筛选最合适的图片
3. 将图片以Markdown格式插入到文档中
4. 在DOCX转换时自动处理图片下载和嵌入

### 使用示例
```json
{
  "action": "generate_long_document",
  "chathistory": "用户对话记录",
  "request": "生成一份关于建筑工程安全管理的详细报告"
}
```

生成的文档将包含：
- 自动检索的相关图片
- 详细的图片描述
- 完整的章节结构
- 多种格式输出

## 系统架构

```
ReactAgent/
├── src/                    # 核心代码
│   ├── document_generator/ # 文档生成工具
│   ├── rag_tool_chroma.py  # RAG工具
│   ├── pdf_parser_tool.py  # PDF解析工具
│   └── tools.py           # 工具注册表
├── frontend/              # Web前端
├── scripts/               # 启动脚本
└── templates/            # 模板文件
```

## 工具详情

### 文档生成工具
- **支持操作**：
  - `generate_long_document` - 生成长篇报告
  - `generate_short_document` - 生成短篇报告
  - `check_status` - 查询生成状态
  - `list_tasks` - 列出所有任务
  - `get_result` - 获取完成结果

### RAG工具
- **支持操作**：
  - `upload_document` - 上传文档
  - `search_documents` - 搜索文档
  - `search_images` - 搜索图片
  - `fill_template_fields` - 填充模板

### PDF解析工具
- **支持操作**：
  - `parse_pdf` - 解析PDF文档
  - `extract_content` - 提取内容
  - `get_structure` - 获取文档结构

## 配置说明

### 主要配置项
- **AI模型**：支持DeepSeek等模型
- **存储服务**：MinIO云存储（已预配置）
- **向量数据库**：ChromaDB
- **图片检索**：集成RAG图片搜索

### 环境变量详情

**必需配置：**
```bash
# AI模型配置
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# 数据库配置
CHROMA_DB_PATH=./rag_storage
```

**MinIO存储配置：**
> ⚠️ **注意**：MinIO配置已在代码中预设，无需额外配置环境变量
> 
> 预设配置：
> - 端点：43.139.19.144:9000
> - 用户名：minioadmin
> - 密码：minioadmin
> - 存储桶：images

## 故障排除

### 常见问题

1. **安装依赖失败**
   ```bash
   # 尝试升级pip
   pip install --upgrade pip
   
   # 分别安装问题依赖
   pip install docling
   pip install camel-ai
   ```

2. **ChromaDB错误**
   ```bash
   # 重新创建数据库
   rm -rf rag_storage
   mkdir rag_storage
   ```

3. **API密钥错误**
   ```bash
   # 检查.env文件
   cat .env
   
   # 验证API密钥格式
   echo $DEEPSEEK_API_KEY
   echo $OPENROUTER_API_KEY
   ```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 更新日志

### v1.3.0 (2025-01-15)
- 🆕 支持Python 3.13
- 🆕 添加完整的环境变量配置
- 🆕 优化依赖管理
- 🆕 增强安装文档
- 🔧 优化MinIO配置说明

### v1.2.0 (2025-01-15)
- 🆕 新增智能图片检索功能
- 🆕 支持图片自动插入到文档
- 🆕 增强DOCX格式的图片支持
- 🔧 优化文档生成流程
- 🐛 修复工具注册表问题

### v1.1.0 (2024-12-20)
- 🆕 新增文档生成工具
- 🆕 支持长短文档生成
- 🆕 集成RAG知识检索
- 🆕 支持多格式输出

### v1.0.0 (2024-11-15)
- 🎉 初始版本发布
- 🆕 基础RAG功能
- 🆕 PDF解析功能
- 🆕 Web界面支持
