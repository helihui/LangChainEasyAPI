# -*- coding: utf-8 -*-
"""
聊天相关的数据模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    model: str = Field("gpt-3.5-turbo", description="使用的模型")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    stream: bool = Field(False, description="是否流式响应")
    tools_enabled: bool = Field(True, description="是否启用工具调用")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: str
    conversation_id: str
    model_used: str
    tokens_used: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None

class ConversationHistory(BaseModel):
    """对话历史模型"""
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    """任务请求模型"""
    task_description: str = Field(..., description="任务描述")
    task_type: str = Field("general", description="任务类型")
    parameters: Optional[Dict[str, Any]] = Field(None, description="任务参数")
    tools: Optional[List[str]] = Field(None, description="指定使用的工具")
    timeout: int = Field(300, description="任务超时时间（秒）")

class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    tools_used: Optional[List[str]] = None
    execution_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now) 