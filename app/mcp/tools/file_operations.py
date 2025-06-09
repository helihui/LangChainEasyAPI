# -*- coding: utf-8 -*-
"""
文件操作工具
"""

import os
import aiofiles
import json
import csv
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path
import mimetypes

from app.mcp.base import MCPTool, ToolMetadata, ToolParameter, ToolResult
from app.core.config import settings
from app.core.logger import logger

class FileReadTool(MCPTool):
    """文件读取工具"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_read",
            description="读取文件内容",
            category="file",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="文件路径",
                    required=True
                ),
                ToolParameter(
                    name="encoding",
                    type="string",
                    description="文件编码",
                    required=False,
                    default="utf-8"
                )
            ],
            tags=["文件", "读取", "I/O"]
        )
    
    async def execute(self, file_path: str, encoding: str = "utf-8") -> ToolResult:
        """读取文件"""
        try:
            file_path = Path(file_path)
            
            # 安全检查
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error="文件不存在"
                )
            
            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    error="路径不是文件"
                )
            
            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size > settings.MAX_FILE_SIZE:
                return ToolResult(
                    success=False,
                    error=f"文件太大，超过限制 {settings.MAX_FILE_SIZE} 字节"
                )
            
            # 检查文件类型
            file_ext = file_path.suffix.lower().lstrip('.')
            if file_ext not in settings.ALLOWED_FILE_TYPES:
                return ToolResult(
                    success=False,
                    error=f"不支持的文件类型: {file_ext}"
                )
            
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content = await f.read()
                
                return ToolResult(
                    success=True,
                    result={
                        "file_path": str(file_path),
                        "content": content,
                        "size": file_size,
                        "encoding": encoding,
                        "mime_type": mimetypes.guess_type(str(file_path))[0]
                    }
                )
        
        except Exception as e:
            logger.error(f"文件读取失败: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            )

class FileWriteTool(MCPTool):
    """文件写入工具"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_write",
            description="写入文件内容",
            category="file",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="文件路径",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="文件内容",
                    required=True
                ),
                ToolParameter(
                    name="encoding",
                    type="string",
                    description="文件编码",
                    required=False,
                    default="utf-8"
                ),
                ToolParameter(
                    name="mode",
                    type="string",
                    description="写入模式",
                    required=False,
                    default="w",
                    enum=["w", "a"]
                )
            ],
            tags=["文件", "写入", "I/O"]
        )
    
    async def execute(self, file_path: str, content: str, encoding: str = "utf-8", mode: str = "w") -> ToolResult:
        """写入文件"""
        try:
            file_path = Path(file_path)
            
            # 创建目录
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 安全检查：确保在允许的目录内
            upload_dir = Path(settings.UPLOAD_DIR)
            try:
                file_path.resolve().relative_to(upload_dir.resolve())
            except ValueError:
                return ToolResult(
                    success=False,
                    error="文件路径不在允许的目录内"
                )
            
            async with aiofiles.open(file_path, mode, encoding=encoding) as f:
                await f.write(content)
                
                return ToolResult(
                    success=True,
                    result={
                        "file_path": str(file_path),
                        "bytes_written": len(content.encode(encoding)),
                        "mode": mode,
                        "encoding": encoding
                    }
                )
        
        except Exception as e:
            logger.error(f"文件写入失败: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            )

class CSVAnalysisTool(MCPTool):
    """CSV分析工具"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="csv_analysis",
            description="分析CSV文件",
            category="data",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="CSV文件路径",
                    required=True
                ),
                ToolParameter(
                    name="operation",
                    type="string",
                    description="操作类型",
                    required=True,
                    enum=["describe", "head", "info", "columns", "shape"]
                ),
                ToolParameter(
                    name="rows",
                    type="integer",
                    description="显示行数（用于head操作）",
                    required=False,
                    default=5
                )
            ],
            tags=["数据", "CSV", "分析"]
        )
    
    async def execute(self, file_path: str, operation: str, rows: int = 5) -> ToolResult:
        """分析CSV文件"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error="文件不存在"
                )
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            result = {"file_path": str(file_path), "operation": operation}
            
            if operation == "describe":
                result["data"] = df.describe().to_dict()
            elif operation == "head":
                result["data"] = df.head(rows).to_dict("records")
            elif operation == "info":
                result["data"] = {
                    "columns": list(df.columns),
                    "dtypes": df.dtypes.to_dict(),
                    "memory_usage": df.memory_usage().to_dict(),
                    "non_null_counts": df.count().to_dict()
                }
            elif operation == "columns":
                result["data"] = list(df.columns)
            elif operation == "shape":
                result["data"] = {"rows": df.shape[0], "columns": df.shape[1]}
            
            return ToolResult(
                success=True,
                result=result
            )
        
        except Exception as e:
            logger.error(f"CSV分析失败: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            ) 