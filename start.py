#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain + FastAPI + MCP 框架启动脚本
"""

import uvicorn
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_directories():
    """创建必要的目录"""
    directories = [
        "logs",
        "data",
        "data/uploads",
        "data/chroma"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 目录创建: {directory}")

def main():
    """主函数"""
    print("🚀 启动 LangChain + FastAPI + MCP 框架")
    print("=" * 50)
    
    # 创建必要目录
    create_directories()
    
    # 检查环境变量文件
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  未找到 .env 文件，请参考 env.example 创建配置文件")
        print("📝 复制命令: cp env.example .env")
        print("🔧 然后编辑 .env 文件配置您的API密钥")
        print()
    
    # 启动服务器
    print("🌐 启动Web服务器...")
    print("📖 API文档: http://localhost:8000/docs")
    print("📚 ReDoc文档: http://localhost:8000/redoc")
    print("🔍 健康检查: http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main() 