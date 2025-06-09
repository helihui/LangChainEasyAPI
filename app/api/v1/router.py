# -*- coding: utf-8 -*-
"""
API v1 主路由
"""

from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.tools import router as tools_router

api_router = APIRouter()

# 包含子路由
api_router.include_router(chat_router, tags=["聊天"])
api_router.include_router(tools_router, tags=["工具"]) 