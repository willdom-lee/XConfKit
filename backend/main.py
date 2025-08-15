from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import init_db
from .routers import devices, backups, strategies
from .scheduler import start_scheduler, stop_scheduler

# 创建FastAPI应用
app = FastAPI(
    title="XConfKit API",
    description="网络设备配置备份管理系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(devices.router)
app.include_router(backups.router)
app.include_router(strategies.router)

# 挂载静态文件（备份文件）
if os.path.exists("./data/backups"):
    app.mount("/backups", StaticFiles(directory="./data/backups"), name="backups")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    start_scheduler()  # 启动备份策略调度器
    print("XConfKit 后端服务已启动")
    print("备份策略调度器已启动")
    print("API文档地址: http://localhost:8000/docs")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "XConfKit API 服务运行中",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时停止调度器"""
    stop_scheduler()
    print("备份策略调度器已停止")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
