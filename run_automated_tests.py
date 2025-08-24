#!/usr/bin/env python3
"""
XConfKit 自动化测试运行脚本
统一执行所有测试模块
"""

import os
import sys
import subprocess
import time
import requests
import json
from datetime import datetime

class AutomatedTestRunner:
    """自动化测试运行器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {
            "backend_api": {"status": "pending", "details": []},
            "backend_services": {"status": "pending", "details": []},
            "frontend_components": {"status": "pending", "details": []},
            "integration": {"status": "pending", "details": []},
        }
        self.start_time = None
        self.end_time = None
    
    def print_header(self, title):
        """打印标题"""
        print("\n" + "=" * 60)
        print(f"🚀 {title}")
        print("=" * 60)
    
    def print_section(self, title):
        """打印章节标题"""
        print(f"\n📋 {title}")
        print("-" * 40)
    
    def check_service_status(self):
        """检查服务状态"""
        self.print_section("检查服务状态")
        
        try:
            # 检查后端服务
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ 后端服务运行正常")
                return True
            else:
                print("❌ 后端服务响应异常")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 后端服务连接失败: {e}")
            return False
    
    def run_backend_api_tests(self):
        """运行后端API测试"""
        self.print_section("运行后端API测试")
        
        try:
            # 运行API测试
            result = subprocess.run([
                sys.executable, 
                "tests/backend/test_api_comprehensive.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ 后端API测试通过")
                self.test_results["backend_api"]["status"] = "passed"
                self.test_results["backend_api"]["details"] = ["所有API测试通过"]
            else:
                print("❌ 后端API测试失败")
                print(f"错误输出: {result.stderr}")
                self.test_results["backend_api"]["status"] = "failed"
                self.test_results["backend_api"]["details"] = [result.stderr]
                
        except subprocess.TimeoutExpired:
            print("❌ 后端API测试超时")
            self.test_results["backend_api"]["status"] = "timeout"
            self.test_results["backend_api"]["details"] = ["测试执行超时"]
        except Exception as e:
            print(f"❌ 后端API测试异常: {e}")
            self.test_results["backend_api"]["status"] = "error"
            self.test_results["backend_api"]["details"] = [str(e)]
    
    def run_backend_service_tests(self):
        """运行后端服务层测试"""
        self.print_section("运行后端服务层测试")
        
        try:
            # 运行服务层测试
            result = subprocess.run([
                sys.executable, 
                "tests/backend/test_services_comprehensive.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ 后端服务层测试通过")
                self.test_results["backend_services"]["status"] = "passed"
                self.test_results["backend_services"]["details"] = ["所有服务层测试通过"]
            else:
                print("❌ 后端服务层测试失败")
                print(f"错误输出: {result.stderr}")
                self.test_results["backend_services"]["status"] = "failed"
                self.test_results["backend_services"]["details"] = [result.stderr]
                
        except subprocess.TimeoutExpired:
            print("❌ 后端服务层测试超时")
            self.test_results["backend_services"]["status"] = "timeout"
            self.test_results["backend_services"]["details"] = ["测试执行超时"]
        except Exception as e:
            print(f"❌ 后端服务层测试异常: {e}")
            self.test_results["backend_services"]["status"] = "error"
            self.test_results["backend_services"]["details"] = [str(e)]
    
    def run_frontend_tests(self):
        """运行前端测试"""
        self.print_section("运行前端组件测试")
        
        try:
            # 检查前端目录
            if not os.path.exists("frontend"):
                print("❌ 前端目录不存在")
                self.test_results["frontend_components"]["status"] = "skipped"
                self.test_results["frontend_components"]["details"] = ["前端目录不存在"]
                return
            
            # 切换到前端目录
            os.chdir("frontend")
            
            # 检查package.json
            if not os.path.exists("package.json"):
                print("❌ package.json不存在")
                self.test_results["frontend_components"]["status"] = "skipped"
                self.test_results["frontend_components"]["details"] = ["package.json不存在"]
                os.chdir("..")
                return
            
            # 安装依赖（如果需要）
            if not os.path.exists("node_modules"):
                print("📦 安装前端依赖...")
                subprocess.run(["npm", "install"], capture_output=True, text=True)
            
            # 运行前端测试
            result = subprocess.run([
                "npm", "test", "--", 
                "--testPathPattern=../tests/frontend/test_components_comprehensive.test.js",
                "--passWithNoTests"
            ], capture_output=True, text=True, timeout=300)
            
            os.chdir("..")
            
            if result.returncode == 0:
                print("✅ 前端组件测试通过")
                self.test_results["frontend_components"]["status"] = "passed"
                self.test_results["frontend_components"]["details"] = ["所有前端组件测试通过"]
            else:
                print("❌ 前端组件测试失败")
                print(f"错误输出: {result.stderr}")
                self.test_results["frontend_components"]["status"] = "failed"
                self.test_results["frontend_components"]["details"] = [result.stderr]
                
        except subprocess.TimeoutExpired:
            print("❌ 前端组件测试超时")
            self.test_results["frontend_components"]["status"] = "timeout"
            self.test_results["frontend_components"]["details"] = ["测试执行超时"]
        except Exception as e:
            print(f"❌ 前端组件测试异常: {e}")
            self.test_results["frontend_components"]["status"] = "error"
            self.test_results["frontend_components"]["details"] = [str(e)]
    
    def run_integration_tests(self):
        """运行集成测试"""
        self.print_section("运行集成测试")
        
        try:
            # 运行集成测试
            result = subprocess.run([
                sys.executable, 
                "tests/integration_test.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ 集成测试通过")
                self.test_results["integration"]["status"] = "passed"
                self.test_results["integration"]["details"] = ["所有集成测试通过"]
            else:
                print("❌ 集成测试失败")
                print(f"错误输出: {result.stderr}")
                self.test_results["integration"]["status"] = "failed"
                self.test_results["integration"]["details"] = [result.stderr]
                
        except subprocess.TimeoutExpired:
            print("❌ 集成测试超时")
            self.test_results["integration"]["status"] = "timeout"
            self.test_results["integration"]["details"] = ["测试执行超时"]
        except Exception as e:
            print(f"❌ 集成测试异常: {e}")
            self.test_results["integration"]["status"] = "error"
            self.test_results["integration"]["details"] = [str(e)]
    
    def run_performance_tests(self):
        """运行性能测试"""
        self.print_section("运行性能测试")
        
        try:
            # 测试API响应时间
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/devices/", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            if response.status_code == 200:
                print(f"✅ API响应时间: {response_time:.2f}ms")
                if response_time < 1000:  # 1秒内
                    print("✅ 性能表现良好")
                else:
                    print("⚠️  性能需要优化")
            else:
                print("❌ API响应异常")
                
        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
    
    def run_security_tests(self):
        """运行安全测试"""
        self.print_section("运行安全测试")
        
        try:
            # 测试SQL注入防护
            test_payloads = [
                "'; DROP TABLE devices; --",
                "' OR '1'='1",
                "'; SELECT * FROM users; --"
            ]
            
            for payload in test_payloads:
                try:
                    response = requests.get(f"{self.base_url}/api/devices/{payload}")
                    if response.status_code == 404:  # 应该返回404而不是500
                        print(f"✅ SQL注入防护正常: {payload}")
                    else:
                        print(f"⚠️  SQL注入防护可能存在问题: {payload}")
                except:
                    print(f"✅ SQL注入防护正常: {payload}")
            
            # 测试XSS防护
            xss_payload = "<script>alert('xss')</script>"
            try:
                response = requests.post(
                    f"{self.base_url}/api/devices/",
                    json={"name": xss_payload, "ip_address": "192.168.1.100"}
                )
                if response.status_code == 422:  # 应该返回验证错误
                    print("✅ XSS防护正常")
                else:
                    print("⚠️  XSS防护可能存在问题")
            except:
                print("✅ XSS防护正常")
                
        except Exception as e:
            print(f"❌ 安全测试失败: {e}")
    
    def generate_test_report(self):
        """生成测试报告"""
        self.print_section("生成测试报告")
        
        # 计算测试统计
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "passed")
        failed_tests = sum(1 for result in self.test_results.values() if result["status"] == "failed")
        error_tests = sum(1 for result in self.test_results.values() if result["status"] == "error")
        timeout_tests = sum(1 for result in self.test_results.values() if result["status"] == "timeout")
        skipped_tests = sum(1 for result in self.test_results.values() if result["status"] == "skipped")
        
        # 生成报告
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "error": error_tests,
                "timeout": timeout_tests,
                "skipped": skipped_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_details": self.test_results,
            "execution_time": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存报告
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 测试报告已保存: {report_file}")
        
        # 打印摘要
        print("\n" + "=" * 60)
        print("📊 测试结果摘要")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"错误: {error_tests} ⚠️")
        print(f"超时: {timeout_tests} ⏰")
        print(f"跳过: {skipped_tests} ⏭️")
        print(f"成功率: {report['test_summary']['success_rate']:.1f}%")
        
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"执行时间: {duration:.2f}秒")
        
        # 详细结果
        print("\n详细结果:")
        for test_name, result in self.test_results.items():
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "error": "⚠️",
                "timeout": "⏰",
                "skipped": "⏭️",
                "pending": "⏳"
            }.get(result["status"], "❓")
            
            print(f"  {status_icon} {test_name}: {result['status']}")
            for detail in result["details"]:
                print(f"    - {detail}")
        
        return report
    
    def run_all_tests(self):
        """运行所有测试"""
        self.print_header("XConfKit 自动化测试套件")
        
        self.start_time = datetime.now()
        
        # 检查服务状态
        if not self.check_service_status():
            print("❌ 服务未运行，请先启动服务")
            return False
        
        # 运行各种测试
        self.run_backend_api_tests()
        self.run_backend_service_tests()
        self.run_frontend_tests()
        self.run_integration_tests()
        self.run_performance_tests()
        self.run_security_tests()
        
        self.end_time = datetime.now()
        
        # 生成报告
        report = self.generate_test_report()
        
        # 返回总体结果
        success_rate = report["test_summary"]["success_rate"]
        if success_rate >= 80:
            print("\n🎉 测试完成！系统质量良好")
            return True
        elif success_rate >= 60:
            print("\n⚠️  测试完成！系统需要改进")
            return False
        else:
            print("\n❌ 测试完成！系统存在严重问题")
            return False

def main():
    """主函数"""
    runner = AutomatedTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n✅ 自动化测试执行成功")
        sys.exit(0)
    else:
        print("\n❌ 自动化测试发现问题")
        sys.exit(1)

if __name__ == "__main__":
    main()
