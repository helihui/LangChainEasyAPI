# -*- coding: utf-8 -*-
"""
FastAPI 主应用程序
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.core.config import Settings
from app.api.v1.router import api_router
from app.core.logger import logger
from app.mcp.tools import *  # 导入并注册所有工具

# 加载环境变量
load_dotenv()

# 获取配置
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    logger.info("🚀 启动 LangChain + FastAPI + MCP 框架")
    yield
    logger.info("🛑 关闭应用程序")

# 创建FastAPI应用
app = FastAPI(
    title="LangChain + MCP 工具调用框架",
    description="基于 FastAPI + LangChain + MCP 的强大而解耦的AI工具调用框架",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "欢迎使用 LangChain + MCP 工具调用框架",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "服务运行正常"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 