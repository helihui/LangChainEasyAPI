# -*- coding: utf-8 -*-
"""
工具相关的API路由
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional

from app.mcp.base import tool_registry
from app.core.logger import logger

router = APIRouter()

@router.get("/tools")
async def list_tools():
    """
    列出所有可用的工具
    """
    try:
        tools_metadata = tool_registry.get_tools_metadata()
        tools_info = []
        
        for metadata in tools_metadata:
            tools_info.append({
                "name": metadata.name,
                "description": metadata.description,
                "category": metadata.category,
                "version": metadata.version,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type,
                        "description": param.description,
                        "required": param.required,
                        "default": param.default,
                        "enum": param.enum
                    }
                    for param in metadata.parameters
                ],
                "tags": metadata.tags
            })
        
        return {
            "tools": tools_info,
            "total_count": len(tools_info)
        }
        
    except Exception as e:
        logger.error(f"获取工具列表错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/categories")
async def list_tool_categories():
    """
    列出工具分类
    """
    try:
        categories = {}
        tools_metadata = tool_registry.get_tools_metadata()
        
        for metadata in tools_metadata:
            category = metadata.category
            if category not in categories:
                categories[category] = []
            categories[category].append(metadata.name)
        
        return {
            "categories": categories,
            "category_count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"获取工具分类错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """
    获取特定工具的详细信息
    """
    try:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        metadata = tool.metadata
        return {
            "name": metadata.name,
            "description": metadata.description,
            "category": metadata.category,
            "version": metadata.version,
            "author": metadata.author,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default,
                    "enum": param.enum
                }
                for param in metadata.parameters
            ],
            "tags": metadata.tags,
            "schema": tool.to_langchain_tool_schema()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具信息错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, parameters: Dict[str, Any]):
    """
    直接执行工具
    
    参数：
    - tool_name: 工具名称
    - parameters: 工具参数
    """
    try:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        # 执行工具
        result = await tool.safe_execute(**parameters)
        
        return {
            "tool_name": tool_name,
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工具错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/category/{category}")
async def get_tools_by_category(category: str):
    """
    按分类获取工具
    """
    try:
        tools = tool_registry.get_tools_by_category(category)
        if not tools:
            return {
                "category": category,
                "tools": [],
                "count": 0
            }
        
        tools_info = []
        for tool in tools:
            metadata = tool.metadata
            tools_info.append({
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "tags": metadata.tags
            })
        
        return {
            "category": category,
            "tools": tools_info,
            "count": len(tools_info)
        }
        
    except Exception as e:
        logger.error(f"按分类获取工具错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/search")
async def search_tools(q: Optional[str] = None, category: Optional[str] = None, tag: Optional[str] = None):
    """
    搜索工具
    
    参数：
    - q: 搜索关键词（在名称和描述中搜索）
    - category: 工具分类
    - tag: 工具标签
    """
    try:
        all_tools = tool_registry.get_tools_metadata()
        filtered_tools = []
        
        for metadata in all_tools:
            # 分类过滤
            if category and metadata.category != category:
                continue
            
            # 标签过滤
            if tag and tag not in metadata.tags:
                continue
            
            # 关键词搜索
            if q:
                search_text = f"{metadata.name} {metadata.description}".lower()
                if q.lower() not in search_text:
                    continue
            
            filtered_tools.append({
                "name": metadata.name,
                "description": metadata.description,
                "category": metadata.category,
                "version": metadata.version,
                "tags": metadata.tags
            })
        
        return {
            "query": {
                "keyword": q,
                "category": category,
                "tag": tag
            },
            "tools": filtered_tools,
            "count": len(filtered_tools)
        }
        
    except Exception as e:
        logger.error(f"搜索工具错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 