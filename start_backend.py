#!/usr/bin/env python
"""
XConfKit 后端启动脚本
"""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    print("启动 XConfKit 后端服务...")
    print("API文档地址: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务")
    
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式自动重载
        log_level="info"
    )
