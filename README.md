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

## 🚀 快速开始

### 1. 环境要求

- Python 3.7+
- 网络连接（需要访问OpenRouter API）

### 2. 安装依赖

```bash
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