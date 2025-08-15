#!/usr/bin/env python3
"""
XConfKit 测试运行脚本
"""

import subprocess
import sys
import os

def run_backend_tests():
    """运行后端测试"""
    print("=" * 50)
    print("运行后端测试...")
    print("=" * 50)
    
    try:
        # 安装测试依赖
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pytest", "httpx"
        ], check=True)
        
        # 运行后端测试
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/backend/", "-v"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"测试运行失败: {e}")
        return False

def run_frontend_tests():
    """运行前端测试"""
    print("=" * 50)
    print("运行前端测试...")
    print("=" * 50)
    
    try:
        # 切换到前端目录
        os.chdir("frontend")
        
        # 安装测试依赖
        subprocess.run([
            "npm", "install", "--save-dev", 
            "@testing-library/react", 
            "@testing-library/jest-dom", 
            "jest", 
            "jest-environment-jsdom"
        ], check=True)
        
        # 运行前端测试
        result = subprocess.run([
            "npm", "test", "--", "--passWithNoTests"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 切换回根目录
        os.chdir("..")
        
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"前端测试运行失败: {e}")
        os.chdir("..")  # 确保切换回根目录
        return False

def run_integration_tests():
    """运行集成测试"""
    print("=" * 50)
    print("运行集成测试...")
    print("=" * 50)
    
    try:
        # 启动后端服务
        print("启动后端服务...")
        backend_process = subprocess.Popen([
            sys.executable, "start_backend.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待后端启动
        import time
        time.sleep(5)
        
        # 测试API连接
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print("✅ 后端服务启动成功")
            else:
                print("❌ 后端服务启动失败")
                return False
        except requests.RequestException as e:
            print(f"❌ 无法连接到后端服务: {e}")
            return False
        
        # 测试设备API
        try:
            response = requests.get("http://localhost:8000/api/devices/", timeout=10)
            if response.status_code == 200:
                print("✅ 设备API测试通过")
            else:
                print("❌ 设备API测试失败")
                return False
        except requests.RequestException as e:
            print(f"❌ 设备API测试失败: {e}")
            return False
        
        # 停止后端服务
        backend_process.terminate()
        backend_process.wait()
        
        return True
        
    except Exception as e:
        print(f"集成测试失败: {e}")
        return False

def main():
    """主函数"""
    print("XConfKit 测试套件")
    print("=" * 50)
    
    # 运行后端测试
    backend_success = run_backend_tests()
    
    # 运行前端测试
    frontend_success = run_frontend_tests()
    
    # 运行集成测试
    integration_success = run_integration_tests()
    
    # 输出结果
    print("=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    print(f"后端测试: {'✅ 通过' if backend_success else '❌ 失败'}")
    print(f"前端测试: {'✅ 通过' if frontend_success else '❌ 失败'}")
    print(f"集成测试: {'✅ 通过' if integration_success else '❌ 失败'}")
    
    if backend_success and frontend_success and integration_success:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
