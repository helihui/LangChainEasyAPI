# -*- coding: utf-8 -*-
"""
MCP工具包初始化
"""

from app.mcp.base import tool_registry
from app.mcp.tools.web_search import GoogleSearchTool, BingSearchTool
from app.mcp.tools.file_operations import FileReadTool, FileWriteTool, CSVAnalysisTool
from app.core.logger import logger

def register_all_tools():
    """注册所有工具"""
    tools_to_register = [
        # Web搜索工具
        GoogleSearchTool(),
        BingSearchTool(),
        
        # 文件操作工具
        FileReadTool(),
        FileWriteTool(),
        CSVAnalysisTool(),
    ]
    
    registered_count = 0
    for tool in tools_to_register:
        try:
            tool_registry.register(tool)
            registered_count += 1
            logger.info(f"✅ 工具注册成功: {tool.metadata.name}")
        except Exception as e:
            logger.error(f"❌ 工具注册失败: {tool.metadata.name} - {str(e)}")
    
    logger.info(f"🎉 工具注册完成，共注册 {registered_count} 个工具")
    return registered_count

# 自动注册工具
register_all_tools() 