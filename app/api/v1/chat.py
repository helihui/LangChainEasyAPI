# -*- coding: utf-8 -*-
"""
聊天相关的API路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import uuid
from datetime import datetime

from app.schemas.chat import ChatRequest, ChatResponse, TaskRequest, TaskResponse
from app.services.langchain_service import langchain_service
from app.mcp.base import tool_registry
from app.core.logger import logger

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    聊天接口
    
    支持功能：
    - 多轮对话
    - 工具调用
    - 上下文记忆
    - 多模型选择
    """
    try:
        response = await langchain_service.chat(request)
        return response
    except Exception as e:
        logger.error(f"聊天接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask_endpoint(message: str, model: str = "gpt-3.5-turbo"):
    """
    简单问答接口
    
    参数：
    - message: 用户消息
    - model: 使用的模型
    """
    try:
        request = ChatRequest(message=message, model=model)
        response = await langchain_service.chat(request)
        
        return {
            "question": message,
            "answer": response.message,
            "model": response.model_used,
            "conversation_id": response.conversation_id,
            "timestamp": response.timestamp
        }
    except Exception as e:
        logger.error(f"问答接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/task", response_model=TaskResponse)
async def task_endpoint(request: TaskRequest):
    """
    任务执行接口
    
    支持功能：
    - 复杂任务处理
    - 工具选择
    - 异步执行
    """
    try:
        task_id = str(uuid.uuid4())
        
        # 执行任务
        result = await langchain_service.execute_task(
            task_description=request.task_description,
            tools=request.tools
        )
        
        return TaskResponse(
            task_id=task_id,
            status="completed" if result["success"] else "failed",
            result=result.get("result"),
            error=result.get("error"),
            tools_used=result.get("tools_used"),
            execution_time=result.get("execution_time")
        )
        
    except Exception as e:
        logger.error(f"任务执行接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    获取对话历史
    """
    try:
        memory = langchain_service.get_memory(conversation_id)
        messages = []
        
        for msg in memory.chat_memory.messages:
            messages.append({
                "role": "user" if hasattr(msg, "content") and isinstance(msg, type(memory.chat_memory.messages[0])) else "assistant",
                "content": msg.content,
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "message_count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"获取对话历史错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    清除对话历史
    """
    try:
        if conversation_id in langchain_service.memory_store:
            del langchain_service.memory_store[conversation_id]
            return {"message": f"对话 {conversation_id} 已清除"}
        else:
            return {"message": "对话不存在"}
            
    except Exception as e:
        logger.error(f"清除对话历史错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    """
    列出可用的模型
    """
    try:
        available_models = []
        
        for client_name, client in langchain_service.llm_clients.items():
            if client_name == "openai":
                available_models.extend([
                    "gpt-3.5-turbo",
                    "gpt-4",
                    "gpt-4-turbo"
                ])
            elif client_name == "anthropic":
                available_models.extend([
                    "claude-3-haiku-20240307",
                    "claude-3-sonnet-20240229",
                    "claude-3-opus-20240229"
                ])
        
        return {
            "available_models": available_models,
            "default_model": "gpt-3.5-turbo"
        }
        
    except Exception as e:
        logger.error(f"获取模型列表错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 