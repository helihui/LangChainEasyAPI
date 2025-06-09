# LangChain + FastAPI + MCP 工具调用框架

这是一个基于 **FastAPI + LangChain + MCP (Model Context Protocol)** 的强大而解耦的AI工具调用框架，支持多种LLM模型和丰富的工具生态系统。

## 🏗️ 架构特点

- **🚀 FastAPI**: 高性能异步Web框架
- **🧠 LangChain**: 强大的LLM应用开发框架
- **🔧 MCP工具系统**: 标准化的工具接口协议
- **🎯 Agent决策**: 智能工具选择和执行
- **💾 对话记忆**: 上下文感知的多轮对话
- **🔌 插件化设计**: 易于扩展的工具生态

## 🛠️ 支持的工具

### 🌐 Web搜索
- Google搜索API
- Bing搜索API

### 📁 文件操作
- 文件读写
- CSV数据分析
- 多格式文件支持

### 📊 数据分析
- Pandas数据处理
- 统计分析
- 数据可视化

### 🗄️ 数据库操作
- SQL查询
- NoSQL操作
- 向量数据库

## 🚀 快速开始

### 1. 环境设置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件，添加您的API密钥
# 至少需要配置一个LLM API密钥（OpenAI或Anthropic）
```

### 3. 启动服务

```bash
# 使用启动脚本
python start.py

# 或直接使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问服务

- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 📡 API接口

### 聊天接口

```bash
# 简单问答
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，请帮我搜索一下Python的最新特性", "model": "gpt-3.5-turbo"}'

# 完整聊天
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "分析一下这个CSV文件的数据",
    "conversation_id": "conv-123",
    "tools_enabled": true
  }'
```

### 任务执行

```bash
curl -X POST "http://localhost:8000/api/v1/task" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "搜索最新的AI技术趋势并生成报告",
    "tools": ["google_search", "file_write"]
  }'
```

### 工具管理

```bash
# 列出所有工具
curl "http://localhost:8000/api/v1/tools"

# 获取工具详情
curl "http://localhost:8000/api/v1/tools/google_search"

# 直接执行工具
curl -X POST "http://localhost:8000/api/v1/tools/google_search/execute" \
  -H "Content-Type: application/json" \
  -d '{"query": "FastAPI tutorial", "num_results": 5}'
```

## 🏗️ 项目结构

```
setup/
├── app/                    # 应用主目录
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── core/              # 核心模块
│   │   ├── config.py      # 配置管理
│   │   └── logger.py      # 日志配置
│   ├── api/               # API路由
│   │   └── v1/
│   │       ├── chat.py    # 聊天接口
│   │       ├── tools.py   # 工具接口
│   │       └── router.py  # 路由汇总
│   ├── schemas/           # 数据模型
│   │   └── chat.py        # 聊天相关模型
│   ├── services/          # 业务服务
│   │   └── langchain_service.py  # LangChain核心服务
│   └── mcp/               # MCP工具系统
│       ├── base.py        # 工具基础类
│       └── tools/         # 具体工具实现
│           ├── web_search.py      # Web搜索工具
│           └── file_operations.py # 文件操作工具
├── data/                  # 数据目录
├── logs/                  # 日志目录
├── requirements.txt       # 项目依赖
├── env.example           # 环境变量模板
├── start.py              # 启动脚本
└── README.md             # 项目说明
```

## 🔧 自定义工具开发

### 1. 创建工具类

```python
from app.mcp.base import MCPTool, ToolMetadata, ToolParameter, ToolResult

class MyCustomTool(MCPTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_tool",
            description="我的自定义工具",
            category="custom",
            parameters=[
                ToolParameter(
                    name="input_text",
                    type="string",
                    description="输入文本",
                    required=True
                )
            ]
        )
    
    async def execute(self, input_text: str) -> ToolResult:
        # 实现工具逻辑
        result = f"处理结果: {input_text}"
        return ToolResult(success=True, result=result)
```

### 2. 注册工具

```python
from app.mcp.base import tool_registry
from my_tools import MyCustomTool

# 注册工具
tool_registry.register(MyCustomTool())
```

## 🌟 特性亮点

- **🔄 异步处理**: 全异步架构，高并发性能
- **🧩 模块化设计**: 松耦合的组件架构
- **🔒 安全可靠**: 参数验证、错误处理、安全检查
- **📊 监控日志**: 完整的日志记录和性能监控
- **🎨 美观界面**: 自动生成的API文档界面
- **🔧 易于扩展**: 标准化的工具开发接口

## 📝 环境变量说明

详细的环境变量配置请参考 `env.example` 文件，主要包括：

- **LLM API配置**: OpenAI、Anthropic、讯飞星火、通义千问
- **工具API配置**: Google搜索、Bing搜索
- **数据库配置**: PostgreSQL、Redis、向量数据库
- **文件存储配置**: 上传目录、文件大小限制
- **日志配置**: 日志级别、日志文件路径

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License 