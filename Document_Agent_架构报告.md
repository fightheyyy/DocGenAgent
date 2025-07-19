# Document_Agent 系统架构报告

> **基于多Agent协作的智能长文档生成系统技术架构分析**

## 📋 系统概述

Document_Agent是一个基于多Agent协作的智能文档生成系统，采用流水线架构，通过三个专门化的Agent协同工作，实现从用户需求到完整专业文档的全流程自动化生成。

### 🎯 核心价值
- **智能规划**：自动分析需求，生成合理的文档结构
- **智能检索**：基于ReAct框架的自适应信息检索
- **智能生成**：高质量的专业内容生成与质量控制
- **高效协作**：三Agent流水线式协作，各司其职

---

## 🏗️ 系统架构

```
用户Query
    ↓
┌─────────────────┐
│ OrchestratorAgent │ → 文档结构规划 + 写作指导
│   (编排代理)      │
└─────────────────┘
    ↓ JSON结构
┌─────────────────┐
│   ReactAgent    │ → 智能检索相关资料
│ (章节写作代理)   │
└─────────────────┘
    ↓ 完整JSON
┌─────────────────┐
│ContentGenerator │ → 并行生成最终内容
│ (内容生成代理)   │
└─────────────────┘
    ↓
最终文档.md
```

---

## 🤖 Agent详细分析

### 1. OrchestratorAgent (编排代理)

#### 📍 **位置**: `Document_Agent/orchestrator_agent/agent.py`

#### 🎯 **核心职责**
1. 分析文档生成目标和需求
2. 解析源文档结构和内容
3. 生成详细的文档大纲
4. 将任务分解为具体的章节规格
5. 协调整个生成流程

#### 🔧 **主要方法**
- `generate_document_structure()` - 生成文档基础结构
- `add_writing_guides()` - 为每个子章节添加写作指导
- `generate_complete_guide()` - 完整流程整合

#### 📝 **核心Prompt模板**

**文档结构生成Prompt**:
```
你是一个资深的专业文档结构设计专家。

用户需求：{user_description}

请为用户设计一个完整、专业的文档结构。你需要：
1. 判断最适合的文档类型
2. 设计合理的章节层级
3. 确定每个章节和子章节的目标

要求：
- 结构完整、逻辑清晰
- 体现项目特点和专业性
- 标题和子标题越多越好，尽可能详细和全面
- 必须按照指定的JSON格式返回

返回JSON格式：
{
  "report_guide": [
    {
      "title": "第一部分 章节标题",
      "goal": "章节目标",
      "sections": [
        {"subtitle": "一、子章节标题"}
      ]
    }
  ]
}
```

**写作指导生成Prompt**:
```
请为这个章节下的每个子章节提供简洁、实用的写作指导。

章节信息：
- 章节标题：{section_title}
- 章节目标：{section_goal}
- 子章节：{subtitles_text}

对于每个子章节，告诉作者：
1. 核心内容要点
2. 关键信息要求  
3. 写作注意事项

要求：
- 内容精炼，重点突出
- 针对性强，贴合项目特点
- 每个子章节的写作指导控制在100-200字内

返回JSON格式包含每个子章节的how_to_write字段
```

#### 🛠️ **使用的工具**
- **LLM客户端**: `OpenRouterClient` - 用于调用语言模型
- **RAG客户端**: `SimpleRAGClient` - 用于检索相关信息
- **并发处理**: `ThreadPoolExecutor` - 并行处理多个章节

#### 📊 **输入输出**
- **输入**: 用户需求描述字符串
- **输出**: 包含完整结构和写作指导的JSON对象

---

### 2. ReactAgent (章节写作代理)

#### 📍 **位置**: `Document_Agent/section_writer_agent/react_agent.py`

#### 🎯 **核心职责**
1. 分析章节信息需求并制定检索策略
2. 执行多轮RAG检索优化
3. 评估检索结果质量
4. 基于反馈调整查询方法
5. 综合高质量信息生成内容

#### 🧠 **ReAct框架实现**

**Reasoning (推理)**: 分析当前章节需求，制定检索策略
**Acting (行动)**: 执行RAG检索，收集相关资料
**Observing (观察)**: 评估检索结果质量
**Reflecting (反思)**: 决定是否继续优化

#### 📝 **核心Prompt模板**

**推理与行动Prompt**:
```
作为一名专业的信息检索分析师，为报告章节制定检索计划。

【目标章节】: {subtitle}
【写作指导】: {how_to_write}
【历史尝试】: 已尝试查询: {attempted_queries}, 历史质量: {quality_scores}
【可用策略】: {available_strategies}

【任务】: 
1. 分析现状
2. 选择一个最佳策略
3. 生成3-5个关键词

【输出格式】: 
{
  "analysis": "简要分析（100字内）",
  "strategy": "选择的策略名称",
  "keywords": "用逗号分隔的关键词"
}
```

#### 🔧 **主要方法**
- `process_report_guide()` - 处理完整报告指南的主入口
- `_react_loop_for_section()` - ReAct核心循环
- `_reason_and_act_for_section()` - 推理与行动
- `_observe_section_results()` - 观察检索结果
- `_reflect()` - 反思与决策

#### 🛠️ **使用的工具**
- **LLM客户端**: `OpenRouterClient` - 用于推理和策略制定
- **RAG检索器**: `SimpleRAGClient` - 执行信息检索
- **并发处理**: `ThreadPoolExecutor` - 并行处理多个章节
- **质量评估**: 内置质量评分机制

#### 📊 **输入输出**
- **输入**: OrchestratorAgent生成的JSON结构
- **输出**: 添加了`retrieved_data`字段的完整JSON

---

### 3. ContentGeneratorAgent (内容生成代理)

#### 📍 **位置**: `Document_Agent/content_generator_agent/simple_agent.py`

#### 🎯 **核心职责**
1. 分析收集到的完美上下文
2. 生成高质量的章节内容
3. 进行多轮质量检查和改进
4. 确保内容的连贯性和准确性
5. 计算和优化内容质量评分

#### 📝 **核心Prompt模板**

**内容生成Prompt**:
```
请严格扮演一位专业的报告撰写人，根据以下信息为一份将提交给政府主管部门和项目委托方的正式报告撰写其中一个章节。

【章节子标题】：{subtitle}
【本章写作目标与角色指引】：{how_to_write}
【核心参考资料】：{retrieved_data}
【改进反馈】：{feedback}

撰写要求与风格指引：

1. 专业角色与语境:
   - 身份定位: 持证的专业评估师
   - 写作目的: 为项目审批提供决策依据
   - 语言风格: 专业、客观、严谨，清晰易读

2. 内容与结构:
   - 紧扣目标: 严格围绕写作指导展开
   - 数据使用: 优先使用参考资料中的直接数据
   - 结构化表达: 采用清晰的层次结构

3. 格式规范:
   - 纯文本格式，无Markdown标记
   - 段落间用空行分隔
   - 使用纯文本序号
   - 字数控制在800-1200字

请直接生成正文内容，不要添加额外说明或标题。
```

#### 🔧 **主要方法**
- `generate_content_from_json()` - 主要生成方法，包含质量控制循环
- `_generate_content_from_json_section()` - 核心生成逻辑
- `_evaluate_content_quality()` - 质量评估与反馈生成

#### 🎯 **质量控制机制**
1. **长度检查**: 200-2000字范围控制
2. **LLM深度评估**: 多维度质量评分
3. **迭代改进**: 基于反馈的多轮优化
4. **阈值控制**: 质量分数达到0.7才通过

#### 🛠️ **使用的工具**
- **LLM客户端**: `OpenRouterClient` - 内容生成和质量评估
- **并发处理**: `MainDocumentGenerator`中的`ThreadPoolExecutor` - 并行生成多个章节
- **质量评估**: 内置多维度评分系统

#### 📊 **输入输出**
- **输入**: 包含`retrieved_data`的完整JSON
- **输出**: 最终的Markdown文档

---

## 🔗 Agent间协作流程

### 阶段1：结构规划 (OrchestratorAgent)
```
用户Query → 文档结构分析 → JSON基础结构
           ↓
      写作指导生成 → 完整JSON结构
```

### 阶段2：智能检索 (ReactAgent)
```
JSON结构 → ReAct循环处理 → 每个章节添加retrieved_data
         ↓
   [推理→行动→观察→反思] × N轮 → 完整带资料的JSON
```

### 阶段3：内容生成 (ContentGeneratorAgent)
```
完整JSON → 并行处理各章节 → 质量控制循环
         ↓
      内容生成 → 质量评估 → 改进迭代 → 最终文档
```

---

## 🛠️ 技术栈与工具

### 🤖 AI模型
- **主模型**: `google\gemini-2.5-flash`
- **API平台**: OpenRouter
- **最大Token**: 10000 (优化后)
- **温度参数**: 0.3 (稳定性优化)

### 🔍 检索系统
- **RAG服务**: `http://43.139.19.144:3001/search`
- **检索策略**: 多策略自适应检索
- **质量评估**: 基于LLM的相关性评分

### ⚡ 并发处理
- **OrchestratorAgent**: 单线程 (稳定性优化)
- **ReactAgent**: 5线程并行
- **ContentGeneratorAgent**: 3线程并行
- **速率限制**: 每4秒一个请求

### 📁 数据格式
- **中间格式**: JSON
- **最终输出**: Markdown
- **编码格式**: UTF-8

---

## 📈 性能特性

### ⏱️ 处理时间
- **结构生成**: 10-30秒
- **智能检索**: 每章节2-5秒 (并行)
- **内容生成**: 每章节30-60秒 (并行)
- **总体时间**: 中等复杂度文档3-8分钟

### 🎯 质量控制
- **多轮优化**: 最多3轮改进
- **质量阈值**: 0.7分 (70%)
- **多维评估**: 长度、完整性、结构性、专业性
- **自动重试**: API失败自动重试机制

### 📊 并发能力
- **支持章节数**: 最多50章节
- **并行线程数**: 3-5线程
- **内存优化**: 流式处理大文档

---

## 🔧 配置与扩展

### 📝 配置文件: `config/settings.py`
```python
SYSTEM_CONFIG = {
    'openrouter': {
        'model': 'deepseek/deepseek-chat-v3-0324:free',
        'max_tokens': 1500,
        'temperature': 0.3
    },
    'agents': {
        'orchestrator': {
            'max_concurrent_workers': 1
        },
        'section_writer': {
            'max_query_rounds': 3
        },
        'content_generator': {
            'max_content_length': 5000,
            'quality_check_rounds': 2
        }
    }
}
```

### 🔌 扩展接口
- **LLM客户端**: 可替换为其他LLM服务
- **RAG系统**: 可接入不同的检索后端
- **输出格式**: 可扩展为PDF、Word等格式
- **Agent架构**: 可增加新的专门化Agent

---

## 🚀 使用示例

### 基本调用
```python
from Document_Agent import OrchestratorAgent, ReactAgent, MainDocumentGenerator

# 初始化客户端
llm_client = OpenRouterClient()
rag_client = SimpleRAGClient()

# 创建Agent流水线
orchestrator = OrchestratorAgent(rag_client, llm_client)
section_writer = ReactAgent(llm_client)
content_generator = MainDocumentGenerator()

# 执行完整流程
user_query = "编写智慧城市技术方案书"
structure = orchestrator.generate_complete_guide(user_query)
enriched = section_writer.process_report_guide(structure)
final_doc = content_generator.generate_document(enriched)
```

### 主程序调用
```bash
# 交互模式
python main.py --interactive

# 直接生成
python main.py --query "为智慧城市项目编写技术方案书"
```

---

## 📋 总结

Document_Agent系统通过三个专门化Agent的协作，实现了从需求分析到最终文档的全流程自动化。每个Agent都有明确的职责分工和优化的Prompt设计，通过ReAct框架、质量控制循环、并发处理等技术，确保生成高质量的专业文档。

### 🎯 核心优势
1. **模块化设计**: 三Agent分工明确，易于维护和扩展
2. **智能化程度高**: ReAct框架的自适应检索和多轮质量优化
3. **性能优化**: 并发处理和配置优化，提高生成效率
4. **专业性强**: 针对政府报告和专业文档的特定优化

### 🔮 技术特色
- **ReAct智能检索**: 自适应策略选择和质量评估
- **多轮质量控制**: 基于反馈的迭代改进机制
- **并发流水线**: 三阶段并行处理，提高整体效率
- **专业化Prompt**: 针对不同文档类型的精准指导 