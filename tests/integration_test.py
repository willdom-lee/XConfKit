#!/usr/bin/env python3
"""
XConfKit 集成测试
测试前后端协作和完整功能流程
"""

import requests
import json
import time
import subprocess
import sys
import os
from typing import Dict, Any

class IntegrationTest:
    """集成测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.backend_process = None
        
    def start_backend(self):
        """启动后端服务"""
        print("启动后端服务...")
        self.backend_process = subprocess.Popen([
            sys.executable, "start_backend.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务启动
        time.sleep(5)
        
        # 检查服务是否启动成功
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ 后端服务启动成功")
                return True
            else:
                print("❌ 后端服务启动失败")
                return False
        except requests.RequestException as e:
            print(f"❌ 无法连接到后端服务: {e}")
            return False
    
    def stop_backend(self):
        """停止后端服务"""
        if self.backend_process:
            print("停止后端服务...")
            self.backend_process.terminate()
            self.backend_process.wait()
    
    def test_health_check(self):
        """测试健康检查"""
        print("\n测试健康检查...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}
            print("✅ 健康检查通过")
            return True
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False
    
    def test_device_management(self):
        """测试设备管理功能"""
        print("\n测试设备管理功能...")
        
        # 1. 获取空设备列表
        try:
            response = requests.get(f"{self.base_url}/api/devices/", timeout=10)
            assert response.status_code == 200
            devices = response.json()
            assert len(devices) == 0
            print("✅ 获取空设备列表成功")
        except Exception as e:
            print(f"❌ 获取设备列表失败: {e}")
            return False
        
        # 2. 创建设备
        device_data = {
            "name": "集成测试设备",
            "ip_address": "192.168.1.100",
            "protocol": "ssh",
            "username": "admin",
            "password": "password123",
            "port": 22,
            "description": "集成测试用设备"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/devices/", 
                json=device_data,
                timeout=10
            )
            assert response.status_code == 200
            created_device = response.json()
            assert created_device["name"] == device_data["name"]
            assert created_device["ip_address"] == device_data["ip_address"]
            device_id = created_device["id"]
            print("✅ 创建设备成功")
        except Exception as e:
            print(f"❌ 创建设备失败: {e}")
            return False
        
        # 3. 获取设备列表
        try:
            response = requests.get(f"{self.base_url}/api/devices/", timeout=10)
            assert response.status_code == 200
            devices = response.json()
            assert len(devices) == 1
            assert devices[0]["id"] == device_id
            print("✅ 获取设备列表成功")
        except Exception as e:
            print(f"❌ 获取设备列表失败: {e}")
            return False
        
        # 4. 获取单个设备
        try:
            response = requests.get(f"{self.base_url}/api/devices/{device_id}", timeout=10)
            assert response.status_code == 200
            device = response.json()
            assert device["id"] == device_id
            assert device["name"] == device_data["name"]
            print("✅ 获取单个设备成功")
        except Exception as e:
            print(f"❌ 获取单个设备失败: {e}")
            return False
        
        # 5. 更新设备
        update_data = {
            "name": "更新后的设备",
            "description": "更新后的描述"
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/api/devices/{device_id}", 
                json=update_data,
                timeout=10
            )
            assert response.status_code == 200
            updated_device = response.json()
            assert updated_device["name"] == "更新后的设备"
            assert updated_device["description"] == "更新后的描述"
            print("✅ 更新设备成功")
        except Exception as e:
            print(f"❌ 更新设备失败: {e}")
            return False
        
        # 6. 测试设备连接（模拟）
        try:
            response = requests.post(f"{self.base_url}/api/devices/{device_id}/test", timeout=10)
            assert response.status_code == 200
            result = response.json()
            # 由于是模拟设备，连接测试应该失败，但API应该正常响应
            print("✅ 设备连接测试API正常")
        except Exception as e:
            print(f"❌ 设备连接测试失败: {e}")
            return False
        
        # 7. 删除设备
        try:
            response = requests.delete(f"{self.base_url}/api/devices/{device_id}", timeout=10)
            assert response.status_code == 200
            result = response.json()
            assert result["success"] == True
            print("✅ 删除设备成功")
        except Exception as e:
            print(f"❌ 删除设备失败: {e}")
            return False
        
        # 8. 验证设备已被删除
        try:
            response = requests.get(f"{self.base_url}/api/devices/{device_id}", timeout=10)
            assert response.status_code == 404
            print("✅ 设备删除验证成功")
        except Exception as e:
            print(f"❌ 设备删除验证失败: {e}")
            return False
        
        return True
    
    def test_backup_management(self):
        """测试备份管理功能"""
        print("\n测试备份管理功能...")
        
        # 1. 先创建一个设备用于备份测试
        device_data = {
            "name": "备份测试设备",
            "ip_address": "192.168.1.200",
            "protocol": "ssh",
            "username": "admin",
            "password": "password123",
            "port": 22
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/devices/", 
                json=device_data,
                timeout=10
            )
            assert response.status_code == 200
            device_id = response.json()["id"]
            print("✅ 创建备份测试设备成功")
        except Exception as e:
            print(f"❌ 创建备份测试设备失败: {e}")
            return False
        
        # 2. 获取空备份列表
        try:
            response = requests.get(f"{self.base_url}/api/backups/", timeout=10)
            assert response.status_code == 200
            backups = response.json()
            assert len(backups) == 0
            print("✅ 获取空备份列表成功")
        except Exception as e:
            print(f"❌ 获取备份列表失败: {e}")
            return False
        
        # 3. 执行备份（应该失败，因为设备不存在或无法连接）
        try:
            response = requests.post(
                f"{self.base_url}/api/backups/execute",
                params={"device_id": device_id, "backup_type": "running-config"},
                timeout=30
            )
            assert response.status_code == 200
            result = response.json()
            # 备份应该失败，但API应该正常响应
            print("✅ 备份执行API正常")
        except Exception as e:
            print(f"❌ 备份执行失败: {e}")
            return False
        
        # 4. 清理测试设备
        try:
            requests.delete(f"{self.base_url}/api/devices/{device_id}", timeout=10)
            print("✅ 清理测试设备成功")
        except Exception as e:
            print(f"⚠️ 清理测试设备失败: {e}")
        
        return True
    
    def run_all_tests(self):
        """运行所有集成测试"""
        print("=" * 60)
        print("XConfKit 集成测试")
        print("=" * 60)
        
        try:
            # 启动后端
            if not self.start_backend():
                return False
            
            # 运行测试
            tests = [
                self.test_health_check,
                self.test_device_management,
                self.test_backup_management,
            ]
            
            passed = 0
            total = len(tests)
            
            for test in tests:
                if test():
                    passed += 1
                else:
                    print(f"❌ 测试 {test.__name__} 失败")
            
            print("\n" + "=" * 60)
            print(f"集成测试结果: {passed}/{total} 通过")
            print("=" * 60)
            
            return passed == total
            
        finally:
            self.stop_backend()

def main():
    """主函数"""
    test = IntegrationTest()
    success = test.run_all_tests()
    
    if success:
        print("\n🎉 所有集成测试通过！")
        return 0
    else:
        print("\n❌ 部分集成测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
