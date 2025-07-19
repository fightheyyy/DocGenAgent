<<<<<<< HEAD
# Gauz文档Agent - 智能长文档生成系统

基于多Agent架构的智能文档生成系统，支持从用户查询到完整专业文档的全流程自动化生成。

## 🌟 系统特性

- **🤖 三Agent协作**：编排代理、章节检索代理、内容生成代理分工合作
- **🧠 智能规划**：自动分析需求，生成合理的文档结构和写作指导
- **🔍 智能检索**：基于ReAct框架的智能资料检索系统
- **📝 专业生成**：高质量的专业文档内容生成
- **⚡ 高效并行**：多线程并行处理，大幅提升生成速度
- **🎯 多样化支持**：支持评估报告、分析报告、方案书、技术文档等

## 🏗️ 系统架构

```
📋 用户Query
    ↓
🏗️ OrchestratorAgent (编排代理)
    ├─ 分析文档需求
    ├─ 生成文档结构
    └─ 制定写作指导
    ↓
🔍 SectionWriterAgent (章节检索代理)
    ├─ ReAct智能推理
    ├─ 多轮检索优化
    └─ 收集相关资料
    ↓
📝 ContentGeneratorAgent (内容生成代理)
    ├─ 并行内容生成
    ├─ 质量评估控制
    └─ 输出最终文档
    ↓
📄 完整专业文档
```
=======
# ReactAgent - 智能文档生成系统

## 系统概述

ReactAgent是一个基于AI的智能文档生成系统，支持多种文档格式的自动生成，包括PDF解析、知识检索、模板填充和文档输出等核心功能。
>>>>>>> b523629ca2a2d0957a76fe426e702bf2067aaa25

## 🚀 快速开始

### 1. 环境要求

<<<<<<< HEAD
- Python 3.7+
- 网络连接（需要访问OpenRouter API）
=======
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
>>>>>>> b523629ca2a2d0957a76fe426e702bf2067aaa25

### 2. 安装依赖

```bash
<<<<<<< HEAD
pip install requests
```

### 3. 基本使用

#### 交互模式（推荐）
```bash
python main.py --interactive
```

#### 直接生成模式
```bash
# 基本用法
python main.py --query "为城市更新项目编写环境影响评估报告"

# 指定输出目录
python main.py --query "白云区文物保护影响评估报告" --output outputs/heritage

# 查看帮助
python main.py --help
```

### 4. 输出文件

系统会在指定目录下生成以下文件：

- `step1_document_guide_YYYYMMDD_HHMMSS.json` - 文档结构和写作指导
- `step2_enriched_guide_YYYYMMDD_HHMMSS.json` - 添加检索资料后的完整指导
- `生成文档的依据_YYYYMMDD_HHMMSS.json` - 内容生成的输入文件
- `完整版文档_YYYYMMDD_HHMMSS.md` - 最终生成的markdown文档

## 📖 使用示例

### 示例1：文物影响评估报告

```bash
python main.py --query "我需要为'白云区鹤边一社吉祥街二巷1号社文体活动中心项目'编写一份文物影响评估报告。项目距离白云区登记保护文物单位'医灵古庙'仅6米，需要评估新建项目对文物的各种影响。"
```

### 示例2：环境影响评估

```bash
python main.py --query "编写城市中心30层综合办公楼建设项目的环境影响评估报告，需要包括交通影响、噪音污染、空气质量等方面的分析。"
```

### 示例3：技术方案书

```bash
python main.py --query "为智慧城市数字化转型项目编写技术实施方案书，包括系统架构、实施计划、风险评估等内容。"
```

## ⚙️ 配置说明

### API配置

系统使用OpenRouter API，配置文件位于 `config/settings.py`：

```python
'openrouter': {
    'api_key': 'your-api-key-here',
    'base_url': 'https://openrouter.ai/api/v1',
    'model': 'deepseek/deepseek-chat-v3-0324:free',
    'max_tokens': 4000,
    'temperature': 0.7,
    'timeout': 30
}
```

### 生成参数

可在配置文件中调整以下参数：

- `max_sections`: 最大章节数
- `parallel_generation`: 是否启用并行生成
- `quality_threshold`: 质量控制阈值
- `max_retries`: 最大重试次数

## 🔧 高级用法

### 程序化调用

```python
from main import DocumentGenerationPipeline

# 创建生成流水线
pipeline = DocumentGenerationPipeline()

# 生成文档
result_files = pipeline.generate_document(
    "编写项目可行性研究报告",
    output_dir="custom_outputs"
)

print(f"生成的文档：{result_files['final_document']}")
```

### 分步执行

如果需要分步执行或自定义流程，可以直接使用各个Agent：

```python
from Document_Agent import OrchestratorAgent, ReactAgent
from Document_Agent.content_generator_agent.main_generator import MainDocumentGenerator

# 步骤1：生成文档结构
orchestrator = OrchestratorAgent(rag_client, llm_client)
structure = orchestrator.generate_complete_guide(user_query)

# 步骤2：智能检索
section_writer = ReactAgent(llm_client)
enriched_structure = section_writer.process_report_guide(structure)

# 步骤3：生成内容
content_generator = MainDocumentGenerator()
final_document = content_generator.generate_document(json_file_path)
```

## 📊 性能说明

- **文档结构生成**：通常需要10-30秒
- **智能检索**：每个章节2-5秒，支持并行处理
- **内容生成**：每个章节30-60秒，3线程并行
- **总体时间**：中等复杂度文档约3-8分钟

## 🎯 适用场景

### 政府报告类
- 环境影响评估报告
- 文物保护影响评估
- 项目可行性研究报告
- 社会稳定风险评估

### 商业文档类
- 商业计划书
- 市场调研报告
- 技术方案书
- 项目投标文件

### 学术技术类
- 技术文档
- 研究报告
- 系统设计文档
- 产品说明书

## 🐛 常见问题

### 1. 导入模块失败
确保在项目根目录下运行程序：
```bash
cd /path/to/Gauz文档Agent
python main.py --interactive
```

### 2. API连接失败
检查网络连接和API配置，确保config/settings.py中的API密钥正确。

### 3. 生成质量不佳
可以尝试：
- 提供更详细的需求描述
- 调整temperature参数（0.3-0.9）
- 修改质量控制阈值

### 4. 生成速度慢
可以调整并行参数：
- 增加线程数（但注意API限制）
- 减少max_tokens以降低生成时间
- 使用更快的模型

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📧 联系

如有问题或建议，请联系项目维护者。 
=======
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
>>>>>>> b523629ca2a2d0957a76fe426e702bf2067aaa25
