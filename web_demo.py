#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain + FastAPI + MCP 框架 Web演示界面
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time

# 页面配置
st.set_page_config(
    page_title="LangChain + MCP 框架演示",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API基础URL
API_BASE_URL = "http://localhost:8000/api/v1"

def check_api_health():
    """检查API服务状态"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_available_tools():
    """获取可用工具列表"""
    try:
        response = requests.get(f"{API_BASE_URL}/tools")
        if response.status_code == 200:
            return response.json()
        return {"tools": [], "total_count": 0}
    except:
        return {"tools": [], "total_count": 0}

def get_available_models():
    """获取可用模型列表"""
    try:
        response = requests.get(f"{API_BASE_URL}/models")
        if response.status_code == 200:
            return response.json()
        return {"available_models": ["gpt-3.5-turbo"], "default_model": "gpt-3.5-turbo"}
    except:
        return {"available_models": ["gpt-3.5-turbo"], "default_model": "gpt-3.5-turbo"}

def send_chat_message(message, model, conversation_id=None, tools_enabled=True):
    """发送聊天消息"""
    try:
        payload = {
            "message": message,
            "model": model,
            "tools_enabled": tools_enabled
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        response = requests.post(f"{API_BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API错误: {response.status_code}"}
    except Exception as e:
        return {"error": f"请求失败: {str(e)}"}

def execute_tool_directly(tool_name, parameters):
    """直接执行工具"""
    try:
        response = requests.post(f"{API_BASE_URL}/tools/{tool_name}/execute", json=parameters)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"工具执行失败: {response.status_code}"}
    except Exception as e:
        return {"error": f"请求失败: {str(e)}"}

# 主界面
def main():
    st.title("🤖 LangChain + FastAPI + MCP 工具调用框架")
    st.markdown("---")
    
    # 检查API服务状态
    api_status = check_api_health()
    if api_status:
        st.success("✅ API服务运行正常")
    else:
        st.error("❌ API服务未启动，请先运行 `python start.py`")
        st.stop()
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # 获取可用模型
        models_data = get_available_models()
        selected_model = st.selectbox(
            "选择模型",
            models_data["available_models"],
            index=0 if models_data["available_models"] else 0
        )
        
        # 工具开关
        tools_enabled = st.checkbox("启用工具调用", value=True)
        
        # 获取工具信息
        tools_data = get_available_tools()
        st.subheader(f"🔧 可用工具 ({tools_data['total_count']})")
        
        for tool in tools_data["tools"]:
            with st.expander(f"{tool['name']} ({tool['category']})"):
                st.write(f"**描述**: {tool['description']}")
                st.write(f"**版本**: {tool['version']}")
                if tool['tags']:
                    st.write(f"**标签**: {', '.join(tool['tags'])}")
    
    # 主要内容区域
    tab1, tab2, tab3 = st.tabs(["💬 智能对话", "🔧 工具测试", "📊 系统信息"])
    
    with tab1:
        st.header("💬 智能对话")
        
        # 对话历史
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = None
        
        # 显示对话历史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "metadata" in message:
                    with st.expander("详细信息"):
                        st.json(message["metadata"])
        
        # 聊天输入
        if prompt := st.chat_input("请输入您的问题..."):
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 发送请求并获取回复
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    response = send_chat_message(
                        prompt, 
                        selected_model, 
                        st.session_state.conversation_id,
                        tools_enabled
                    )
                
                if "error" in response:
                    st.error(f"错误: {response['error']}")
                else:
                    st.markdown(response["message"])
                    
                    # 保存对话ID
                    st.session_state.conversation_id = response["conversation_id"]
                    
                    # 添加助手消息
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response["message"],
                        "metadata": {
                            "model": response["model_used"],
                            "processing_time": response.get("processing_time"),
                            "conversation_id": response["conversation_id"]
                        }
                    })
        
        # 清除对话按钮
        if st.button("🗑️ 清除对话"):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.rerun()
    
    with tab2:
        st.header("🔧 工具测试")
        
        if tools_data["tools"]:
            # 选择工具
            tool_names = [tool["name"] for tool in tools_data["tools"]]
            selected_tool_name = st.selectbox("选择要测试的工具", tool_names)
            
            # 获取选中工具的详细信息
            selected_tool = next(tool for tool in tools_data["tools"] if tool["name"] == selected_tool_name)
            
            st.subheader(f"工具: {selected_tool['name']}")
            st.write(f"**描述**: {selected_tool['description']}")
            st.write(f"**分类**: {selected_tool['category']}")
            
            # 参数输入
            st.subheader("参数配置")
            parameters = {}
            
            for param in selected_tool["parameters"]:
                param_name = param["name"]
                param_type = param["type"]
                param_desc = param["description"]
                param_required = param["required"]
                param_default = param.get("default")
                
                label = f"{param_name} ({'必需' if param_required else '可选'})"
                help_text = param_desc
                
                if param_type == "string":
                    if param.get("enum"):
                        parameters[param_name] = st.selectbox(
                            label, 
                            param["enum"], 
                            help=help_text
                        )
                    else:
                        parameters[param_name] = st.text_input(
                            label, 
                            value=param_default or "", 
                            help=help_text
                        )
                elif param_type == "integer":
                    parameters[param_name] = st.number_input(
                        label, 
                        value=param_default or 0, 
                        step=1, 
                        help=help_text
                    )
                elif param_type == "boolean":
                    parameters[param_name] = st.checkbox(
                        label, 
                        value=param_default or False, 
                        help=help_text
                    )
            
            # 执行工具
            if st.button("🚀 执行工具"):
                with st.spinner("执行中..."):
                    result = execute_tool_directly(selected_tool_name, parameters)
                
                if "error" in result:
                    st.error(f"执行失败: {result['error']}")
                else:
                    st.success("✅ 执行成功")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("执行时间", f"{result.get('execution_time', 0):.2f}s")
                    with col2:
                        st.metric("状态", "成功" if result["success"] else "失败")
                    
                    if result["success"] and result["result"]:
                        st.subheader("执行结果")
                        if isinstance(result["result"], (dict, list)):
                            st.json(result["result"])
                        else:
                            st.text(result["result"])
                    
                    if result.get("error"):
                        st.error(f"错误信息: {result['error']}")
        else:
            st.warning("暂无可用工具")
    
    with tab3:
        st.header("📊 系统信息")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 模型信息")
            st.json(models_data)
        
        with col2:
            st.subheader("🔧 工具统计")
            if tools_data["tools"]:
                # 按分类统计
                categories = {}
                for tool in tools_data["tools"]:
                    cat = tool["category"]
                    categories[cat] = categories.get(cat, 0) + 1
                
                st.json(categories)
            else:
                st.write("暂无工具数据")
        
        # API端点信息
        st.subheader("🌐 API端点")
        endpoints = [
            {"方法": "POST", "路径": "/api/v1/chat", "描述": "智能对话"},
            {"方法": "POST", "路径": "/api/v1/ask", "描述": "简单问答"},
            {"方法": "POST", "路径": "/api/v1/task", "描述": "任务执行"},
            {"方法": "GET", "路径": "/api/v1/tools", "描述": "工具列表"},
            {"方法": "GET", "路径": "/api/v1/models", "描述": "模型列表"},
        ]
        st.table(endpoints)

if __name__ == "__main__":
    main() 