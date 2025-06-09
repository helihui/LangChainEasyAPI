# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 工具基础类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio

class ToolParameter(BaseModel):
    """工具参数模型"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None

class ToolMetadata(BaseModel):
    """工具元数据"""
    name: str
    description: str
    parameters: List[ToolParameter]
    category: str = "general"
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = []

class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class MCPTool(ABC):
    """MCP工具基础类"""
    
    def __init__(self):
        self._metadata: Optional[ToolMetadata] = None
        self._initialized = False
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """返回工具元数据"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具逻辑"""
        pass
    
    async def initialize(self) -> bool:
        """初始化工具"""
        print(f"初始化状态: {self._initialized}")
        if not self._initialized:
            try:
                await self._initialize()
                self._initialized = True
                print(f"初始化完成: {self._initialized}")
                return True
            except Exception as e:
                print(f"初始化失败: {self._initialized}")
                return False
        return True
    
    async def _initialize(self):
        """子类可重写此方法进行特定初始化"""
        pass
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """验证参数"""
        validated = {}
        for param in self.metadata.parameters:
            value = kwargs.get(param.name)
            
            if param.required and value is None:
                raise ValueError(f"缺少必需参数: {param.name}")
            
            if value is None and param.default is not None:
                value = param.default
            
            if value is not None:
                if param.enum and value not in param.enum:
                    raise ValueError(f"参数 {param.name} 值必须在 {param.enum} 中")
                
                validated[param.name] = value
        
        return validated
    
    async def safe_execute(self, **kwargs) -> ToolResult:
        """安全执行工具"""
        start_time = datetime.now()
        
        try:
            # 初始化工具
            if not await self.initialize():
                return ToolResult(
                    success=False,
                    error="工具初始化失败"
                )
            
            # 验证参数
            validated_params = self.validate_parameters(**kwargs)
            
            # 执行工具
            result = await self.execute(**validated_params)
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def to_langchain_tool_schema(self) -> Dict[str, Any]:
        """转换为LangChain工具模式"""
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                        **({"enum": param.enum} if param.enum else {}),
                        **({"default": param.default} if param.default is not None else {})
                    }
                    for param in self.metadata.parameters
                },
                "required": [param.name for param in self.metadata.parameters if param.required]
            }
        }

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: MCPTool):
        """注册工具"""
        tool_name = tool.metadata.name
        tool_category = tool.metadata.category
        
        self._tools[tool_name] = tool
        
        if tool_category not in self._categories:
            self._categories[tool_category] = []
        
        if tool_name not in self._categories[tool_category]:
            self._categories[tool_category].append(tool_name)
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: str) -> List[MCPTool]:
        """按类别获取工具"""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names]
    
    def list_all_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())
    
    def get_tools_metadata(self) -> List[ToolMetadata]:
        """获取所有工具的元数据"""
        return [tool.metadata for tool in self._tools.values()]
    
    def get_langchain_tools_schema(self) -> List[Dict[str, Any]]:
        """获取LangChain工具模式"""
        return [tool.to_langchain_tool_schema() for tool in self._tools.values()]

# 全局工具注册表
tool_registry = ToolRegistry() 