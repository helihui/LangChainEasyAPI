# -*- coding: utf-8 -*-
"""
LangChain 核心服务
"""

from typing import Dict, List, Any, Optional, AsyncGenerator
import json
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory

from app.core.config import settings
from app.core.logger import logger
from app.mcp.base import tool_registry, ToolResult
from app.schemas.chat import ChatMessage, MessageRole, ChatRequest, ChatResponse

class LangChainService:
    """LangChain 核心服务"""
    
    def __init__(self):
        self.llm_clients = {}
        self.memory_store = {}  # 简单的内存存储，生产环境应使用Redis
        self._initialize_llms()
        self._setup_agent()
    
    def _initialize_llms(self):
        """初始化LLM客户端"""
        try:
            # OpenAI
            if settings.OPENAI_API_KEY:
                self.llm_clients["openai"] = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_API_BASE,
                    model="gpt-3.5-turbo",
                    temperature=0.7
                )
                logger.info("✅ OpenAI LLM 初始化成功")
            
            # Anthropic
            if settings.ANTHROPIC_API_KEY:
                self.llm_clients["anthropic"] = ChatAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                    model="claude-3-haiku-20240307",
                    temperature=0.7
                )
                logger.info("✅ Anthropic LLM 初始化成功")
                
        except Exception as e:
            logger.error(f"LLM初始化失败: {str(e)}")
    
    def _setup_agent(self):
        """设置Agent"""
        try:
            # 创建工具列表
            self.tools = self._create_langchain_tools()
            
            # 设置提示模板
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个强大的AI助手，能够调用各种工具来帮助用户完成任务。

可用工具：
{tools}

使用工具时，请按照以下格式：
- 仔细分析用户的需求
- 选择合适的工具
- 正确传递参数
- 根据工具结果给出有用的回应

请用中文回复用户。"""),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            
            logger.info(f"✅ Agent设置完成，可用工具数量: {len(self.tools)}")
            
        except Exception as e:
            logger.error(f"Agent设置失败: {str(e)}")
            self.tools = []
    
    def _create_langchain_tools(self) -> List:
        """创建LangChain工具"""
        langchain_tools = []
        
        # 获取所有注册的MCP工具
        for tool_name in tool_registry.list_all_tools():
            mcp_tool = tool_registry.get_tool(tool_name)
            if mcp_tool:
                # 创建LangChain工具包装器
                langchain_tool = self._wrap_mcp_tool(mcp_tool)
                langchain_tools.append(langchain_tool)
        
        return langchain_tools
    
    def _wrap_mcp_tool(self, mcp_tool):
        """将MCP工具包装为LangChain工具"""
        schema = mcp_tool.to_langchain_tool_schema()
        
        @tool(schema["name"], return_direct=False)
        async def wrapped_tool(**kwargs) -> str:
            """工具包装器"""
            try:
                result = await mcp_tool.safe_execute(**kwargs)
                
                if result.success:
                    return json.dumps(result.result, ensure_ascii=False, indent=2)
                else:
                    return f"工具执行失败: {result.error}"
                    
            except Exception as e:
                return f"工具执行异常: {str(e)}"
        
        # 设置工具描述
        wrapped_tool.__doc__ = schema["description"]
        wrapped_tool.name = schema["name"]
        
        return wrapped_tool
    
    def get_llm(self, model_name: str):
        """获取LLM客户端"""
        if model_name.startswith("gpt"):
            return self.llm_clients.get("openai")
        elif model_name.startswith("claude"):
            return self.llm_clients.get("anthropic")
        else:
            # 默认返回第一个可用的LLM
            return next(iter(self.llm_clients.values()), None)
    
    def get_memory(self, conversation_id: str) -> ConversationBufferWindowMemory:
        """获取对话记忆"""
        if conversation_id not in self.memory_store:
            self.memory_store[conversation_id] = ConversationBufferWindowMemory(
                k=10,  # 保持最近10轮对话
                return_messages=True,
                memory_key="chat_history"
            )
        return self.memory_store[conversation_id]
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """处理聊天请求"""
        try:
            start_time = datetime.now()
            
            # 生成对话ID
            if not request.conversation_id:
                request.conversation_id = str(uuid.uuid4())
            
            # 获取LLM
            llm = self.get_llm(request.model)
            if not llm:
                return ChatResponse(
                    message="暂无可用的LLM服务",
                    conversation_id=request.conversation_id,
                    model_used=request.model
                )
            
            # 获取记忆
            memory = self.get_memory(request.conversation_id)
            
            # 创建Agent执行器
            if request.tools_enabled and self.tools:
                agent = create_tool_calling_agent(llm, self.tools, self.prompt)
                agent_executor = AgentExecutor(
                    agent=agent, 
                    tools=self.tools, 
                    memory=memory,
                    verbose=True,
                    handle_parsing_errors=True
                )
                
                # 执行Agent
                result = await agent_executor.ainvoke({
                    "input": request.message
                })
                
                response_message = result.get("output", "抱歉，我无法处理这个请求。")
                
            else:
                # 直接使用LLM，不调用工具
                messages = []
                
                # 添加系统消息
                messages.append(SystemMessage(content="你是一个有用的AI助手，请用中文回复。"))
                
                # 添加历史消息
                chat_history = memory.chat_memory.messages
                messages.extend(chat_history)
                
                # 添加用户消息
                messages.append(HumanMessage(content=request.message))
                
                # 调用LLM
                response = await llm.ainvoke(messages)
                response_message = response.content
                
                # 保存到记忆
                memory.chat_memory.add_user_message(request.message)
                memory.chat_memory.add_ai_message(response_message)
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                message=response_message,
                conversation_id=request.conversation_id,
                model_used=request.model,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"聊天处理失败: {str(e)}")
            return ChatResponse(
                message=f"处理请求时发生错误: {str(e)}",
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                model_used=request.model
            )
    
    async def execute_task(self, task_description: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """执行特定任务"""
        try:
            start_time = datetime.now()
            
            # 选择工具
            available_tools = self.tools
            if tools:
                # 过滤指定的工具
                available_tools = [t for t in self.tools if t.name in tools]
            
            # 获取默认LLM
            llm = next(iter(self.llm_clients.values()), None)
            if not llm:
                return {
                    "success": False,
                    "error": "暂无可用的LLM服务"
                }
            
            if available_tools:
                # 创建Agent
                agent = create_tool_calling_agent(llm, available_tools, self.prompt)
                agent_executor = AgentExecutor(
                    agent=agent,
                    tools=available_tools,
                    verbose=True,
                    handle_parsing_errors=True
                )
                
                # 执行任务
                result = await agent_executor.ainvoke({
                    "input": task_description
                })
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "success": True,
                    "result": result.get("output"),
                    "tools_used": [t.name for t in available_tools],
                    "execution_time": execution_time
                }
            else:
                # 直接使用LLM
                response = await llm.ainvoke([HumanMessage(content=task_description)])
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "success": True,
                    "result": response.content,
                    "tools_used": [],
                    "execution_time": execution_time
                }
                
        except Exception as e:
            logger.error(f"任务执行失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# 创建全局服务实例
langchain_service = LangChainService() 