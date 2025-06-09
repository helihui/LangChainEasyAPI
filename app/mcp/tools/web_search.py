# -*- coding: utf-8 -*-
"""
Web搜索工具
"""

import aiohttp
import json
from typing import Dict, Any, List
from datetime import datetime

from app.mcp.base import MCPTool, ToolMetadata, ToolParameter, ToolResult
from app.core.config import settings
from app.core.logger import logger

class GoogleSearchTool(MCPTool):
    """Google搜索工具"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="google_search",
            description="使用Google搜索API搜索网络信息",
            category="web",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="搜索查询词",
                    required=True
                ),
                ToolParameter(
                    name="num_results",
                    type="integer",
                    description="返回结果数量",
                    required=False,
                    default=5
                ),
                ToolParameter(
                    name="lang",
                    type="string",
                    description="搜索语言",
                    required=False,
                    default="zh-CN"
                )
            ],
            tags=["搜索", "网络", "信息获取"]
        )
    
    async def _initialize(self):
        """检查API密钥"""
        if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
            raise ValueError("Google API密钥或CSE ID未配置")
    
    async def execute(self, query: str, num_results: int = 5, lang: str = "zh-CN") -> ToolResult:
        """执行Google搜索"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": settings.GOOGLE_API_KEY,
                "cx": settings.GOOGLE_CSE_ID,
                "q": query,
                "num": min(num_results, 10),
                "lr": lang
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get("items", []):
                            results.append({
                                "title": item.get("title"),
                                "link": item.get("link"),
                                "snippet": item.get("snippet"),
                                "displayLink": item.get("displayLink")
                            })
                        
                        return ToolResult(
                            success=True,
                            result={
                                "query": query,
                                "results": results,
                                "total_results": data.get("searchInformation", {}).get("totalResults"),
                                "search_time": data.get("searchInformation", {}).get("searchTime")
                            }
                        )
                    else:
                        error_data = await response.json()
                        return ToolResult(
                            success=False,
                            error=f"搜索失败: {error_data.get('error', {}).get('message', '未知错误')}"
                        )
        
        except Exception as e:
            logger.error(f"Google搜索执行失败: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            )

class BingSearchTool(MCPTool):
    """Bing搜索工具"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="bing_search",
            description="使用Bing搜索API搜索网络信息", 
            category="web",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string", 
                    description="搜索查询词",
                    required=True
                ),
                ToolParameter(
                    name="count",
                    type="integer",
                    description="返回结果数量",
                    required=False,
                    default=5
                ),
                ToolParameter(
                    name="market",
                    type="string",
                    description="市场代码",
                    required=False,
                    default="zh-CN"
                )
            ],
            tags=["搜索", "网络", "信息获取"]
        )
    
    async def _initialize(self):
        """检查API密钥"""
        if not settings.BING_API_KEY:
            raise ValueError("Bing API密钥未配置")
    
    async def execute(self, query: str, count: int = 5, market: str = "zh-CN") -> ToolResult:
        """执行Bing搜索"""
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {
                "Ocp-Apim-Subscription-Key": settings.BING_API_KEY
            }
            params = {
                "q": query,
                "count": min(count, 50),
                "mkt": market,
                "responseFilter": "webPages"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        web_pages = data.get("webPages", {})
                        results = []
                        
                        for item in web_pages.get("value", []):
                            results.append({
                                "title": item.get("name"),
                                "url": item.get("url"),
                                "snippet": item.get("snippet"),
                                "displayUrl": item.get("displayUrl"),
                                "dateLastCrawled": item.get("dateLastCrawled")
                            })
                        
                        return ToolResult(
                            success=True,
                            result={
                                "query": query,
                                "results": results,
                                "total_estimated_matches": web_pages.get("totalEstimatedMatches")
                            }
                        )
                    else:
                        error_text = await response.text()
                        return ToolResult(
                            success=False,
                            error=f"Bing搜索失败: {error_text}"
                        )
        
        except Exception as e:
            logger.error(f"Bing搜索执行失败: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            ) 