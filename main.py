#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weirdhost 登录脚本 - GitHub Actions 版本
修正版 - 修复Cookie处理问题
"""

import os
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError


class WeirdhostLogin:
    def __init__(self):
        """初始化，从环境变量读取配置"""
        self.url = os.getenv('WEIRDHOST_URL', 'https://hub.weirdhost.xyz')
        self.server_urls = os.getenv('WEIRDHOST_SERVER_URLS', '')
        self.login_url = os.getenv('WEIRDHOST_LOGIN_URL', 'https://hub.weirdhost.xyz/auth/login')
        
        # 获取认证信息 - 修复Cookie获取方式
        self.cookies_str = os.getenv('WEIRDHOST_COOKIES', '')
        self.email = os.getenv('WEIRDHOST_EMAIL', '')
        self.password = os.getenv('WEIRDHOST_PASSWORD', '')
        
        # 浏览器配置
        self.headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        
        # 解析服务器URL列表
        self.server_list = []
        if self.server_urls:
            self.server_list = [url.strip() for url in self.server_urls.split(',') if url.strip()]
        
        # 解析Cookie字符串
        self.cookies_dict = self.parse_cookies(self.cookies_str)
    
    def parse_cookies(self, cookies_str):
        """解析Cookie字符串"""
        cookies = {}
        if not cookies_str:
            return cookies
            
        for cookie in cookies_str.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value
                
        return cookies
    
    def log(self, message, level="INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def has_cookie_auth(self):
        """检查是否有 cookie 认证信息"""
        return bool(self.cookies_dict)
    
    def has_email_auth(self):
        """检查是否有邮箱密码认证信息"""
        return bool(self.email and self.password)
    
    def check_login_status(self, page):
        """检查是否已登录"""
        try:
            self.log("检查登录状态...")
            
            # 检查页面内容判断登录状态
            page_content = page.content().lower()
            
            # 如果页面包含登录相关元素，说明未登录
            if any(text in page_content for text in ['login', 'sign in', '登录', 'email', 'password', 'username']):
                self.log("检测到登录页面元素，未登录")
                return False
            else:
                self.log("未检测到登录页面元素，判断为已登录")
                return True
                
        except Exception as e:
            self.log(f"检查登录状态时出错: {e}", "ERROR")
            return False
    
    def login_with_cookies(self, context):
        """使用 Cookies 登录 - 修复版"""
        try:
            self.log("尝试使用 Cookies 登录...")
            
            if not self.cookies_dict:
                self.log("没有可用的Cookie信息", "ERROR")
                return False
            
            cookies_to_add = []
            
            # 添加所有解析到的Cookie
            for name, value in self.cookies_dict.items():
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'Lax'
                }
                cookies_to_add.append(cookie)
                self.log(f"已添加 {name} cookie")
            
            if cookies_to_add:
                context.add_cookies(cookies_to_add)
                self.log(f"成功添加 {len(cookies_to_add)} 个Cookie")
                return True
            else:
                self.log("没有有效的Cookie可添加", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"设置 Cookies 时出错: {e}", "ERROR")
            return False
    
    def login_with_email(self, page):
        """使用邮箱密码登录"""
        try:
            self.log("尝试使用邮箱密码登录...")
            
            # 访问登录页面
            self.log(f"访问登录页面: {self.login_url}")
            page.goto(self.login_url, wait_until="domcontentloaded")
            
            # 使用多种可能的选择器
            email_selectors = ['input[name="username"]', 'input[name="email"]', 'input[type="email"]']
            password_selectors = ['input[name="password"]', 'input[type="password"]']
            login_button_selectors = ['button[type="submit"]', 'button:has-text("Login")', 'button:has-text("登录")']
            
            # 查找有效的选择器
            email_field = None
            password_field = None
            login_button = None
            
            for selector in email_selectors:
                try:
                    email_field = page.locator(selector)
                    if email_field.count() > 0:
                        break
                except:
                    continue
            
            for selector in password_selectors:
                try:
                    password_field = page.locator(selector)
                    if password_field.count() > 0:
                        break
                except:
                    continue
            
            for selector in login_button_selectors:
                try:
                    login_button = page.locator(selector)
                    if login_button.count() > 0:
                        break
                except:
                    continue
            
            if not email_field or not password_field or not login_button:
                self.log("找不到登录表单元素", "ERROR")
                return False
            
            # 填写登录信息
            self.log("填写邮箱和密码...")
            email_field.fill(self.email)
            password_field.fill(self.password)
            
            # 点击登录并等待导航
            self.log("点击登录按钮...")
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                login_button.click()
            
            # 检查登录是否成功
            time.sleep(3)  # 等待页面稳定
            if self.check_login_status(page):
                self.log("邮箱密码登录成功！")
                return True
            else:
                self.log("邮箱密码登录失败", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"邮箱密码登录时出错: {e}", "ERROR")
            return False
    
    def process_server(self, page, server_url):
        """处理单个服务器的续期操作"""
        server_id = server_url.split('/')[-1] if server_url else "unknown"
        self.log(f"开始处理服务器 {server_id}")
        
        try:
            # 访问服务器页面
            self.log(f"访问服务器页面: {server_url}")
            page.goto(server_url, wait_until="networkidle")
            time.sleep(3)
            
            # 检查是否已登录
            if not self.check_login_status(page):
                self.log(f"服务器 {server_id} 未登录，尝试重新登录", "WARNING")
                return f"{server_id}: login_failed"
            
            # 查找续期按钮
            button_selectors = [
                'button:has-text("시간추가")',
                'button:has-text("시간 추가")',
                '//button[contains(text(), "시간추가")]',
                '//button[contains(text(), "시간 추가")]',
            ]
            
            renew_button = None
            for selector in button_selectors:
                try:
                    if selector.startswith('//'):
                        button = page.locator(f'xpath={selector}')
                    else:
                        button = page.locator(selector)
                    
                    if button.count() > 0 and button.first.is_visible():
                        renew_button = button.first
                        self.log(f"找到续期按钮: {selector}")
                        break
                except:
                    continue
            
            if not renew_button:
                # 尝试查找所有按钮
                try:
                    all_buttons = page.locator('button')
                    for i in range(all_buttons.count()):
                        button = all_buttons.nth(i)
                        if button.is_visible():
                            text = button.text_content()
                            if text and "시간" in text:
                                renew_button = button
                                self.log("通过文本搜索找到续期按钮")
                                break
                except:
                    pass
            
            if not renew_button:
                self.log(f"服务器 {server_id} 未找到续期按钮")
                return f"{server_id}: no_button_found"
            
            # 点击续期按钮
            if renew_button.is_enabled():
                self.log(f"点击续期按钮...")
                renew_button.click()
                time.sleep(5)
                
                # 简单的成功判断
                page_content = page.content()
                if "성공" in page_content or "success" in page_content.lower():
                    self.log(f"服务器 {server_id} 续期成功")
                    return f"{server_id}: success"
                elif "이미" in page_content or "already" in page_content.lower():
                    self.log(f"服务器 {server_id} 已经续期过了")
                    return f"{server_id}: already_renewed"
                else:
                    self.log(f"服务器 {server_id} 续期结果未知")
                    return f"{server_id}: unknown"
            else:
                self.log(f"服务器 {server_id} 续期按钮不可点击")
                return f"{server_id}: button_disabled"
                
        except Exception as e:
            self.log(f"处理服务器 {server_id} 时出错: {e}", "ERROR")
            return f"{server_id}: error"
    
    def run(self):
        """主运行函数"""
        self.log("开始 Weirdhost 自动续期任务")
        
        # 检查认证信息
        has_cookie = self.has_cookie_auth()
        has_email = self.has_email_auth()
        
        self.log(f"Cookie 认证可用: {has_cookie}")
        self.log(f"邮箱密码认证可用: {has_email}")
        self.log(f"解析到的Cookie: {list(self.cookies_dict.keys())}")
        
        if not has_cookie and not has_email:
            self.log("没有可用的认证信息！", "ERROR")
            return ["error: no_auth"]
        
        # 检查服务器URL列表
        if not self.server_list:
            self.log("未设置服务器URL列表！请设置 WEIRDHOST_SERVER_URLS 环境变量", "ERROR")
            return ["error: no_servers"]
        
        self.log(f"需要处理的服务器数量: {len(self.server_list)}")
        for i, server_url in enumerate(self.server_list, 1):
            self.log(f"服务器 {i}: {server_url}")
        
        results = []
        
        try:
            with sync_playwright() as p:
                # 启动浏览器
                browser = p.chromium.launch(headless=self.headless)
                
                # 创建浏览器上下文
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(60000)
                
                login_success = False
                
                # 方案1: 尝试 Cookie 登录
                if has_cookie:
                    if self.login_with_cookies(context):
                        # 访问首页检查登录状态
                        self.log("检查Cookie登录状态...")
                        page.goto(self.url, wait_until="networkidle")
                        time.sleep(3)
                        
                        if self.check_login_status(page):
                            self.log("✅ Cookie 登录成功！")
                            login_success = True
                        else:
                            self.log("Cookie 登录失败，cookies 可能已过期", "WARNING")
                
                # 方案2: 如果 Cookie 登录失败，尝试邮箱密码登录
                if not login_success and has_email:
                    if self.login_with_email(page):
                        login_success = True
                
                # 如果登录成功，依次处理每个服务器
                if login_success:
                    for server_url in self.server_list:
                        result = self.process_server(page, server_url)
                        results.append(result)
                        self.log(f"服务器处理结果: {result}")
                        
                        # 在处理下一个服务器前等待一下
                        time.sleep(3)
                else:
                    self.log("❌ 所有登录方式都失败了", "ERROR")
                    results = ["login_failed"]
                
                browser.close()
                return results
                
        except TimeoutError as e:
            self.log(f"操作超时: {e}", "ERROR")
            return ["error: timeout"]
        except Exception as e:
            self.log(f"运行时出错: {e}", "ERROR")
            return ["error: runtime"]
    
    def write_readme_file(self, results):
        """写入README文件"""
        try:
            from datetime import datetime, timezone, timedelta
            beijing_time = datetime.now(timezone(timedelta(hours=8)))
            timestamp = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
            
            status_messages = {
                "success": "✅ 续期成功",
                "already_renewed": "⚠️ 已经续期过了", 
                "no_button_found": "❌ 未找到续期按钮",
                "button_disabled": "❌ 续期按钮不可点击",
                "login_failed": "❌ 登录失败",
                "error": "💥 运行出错",
                "unknown": "❓ 结果未知"
            }
            
            readme_content = f"""# Weirdhost 自动续期脚本

**最后运行时间**: `{timestamp}` (北京时间)

## 运行结果

"""
            
            for result in results:
                if ":" in result:
                    server_id, status = result.split(":", 1)
                    status_msg = status_messages.get(status.strip(), f"❓ 未知状态 ({status})")
                    readme_content += f"- 服务器 `{server_id}`: {status_msg}\n"
                else:
                    status_msg = status_messages.get(result, f"❓ 未知状态 ({result})")
                    readme_content += f"- {status_msg}\n"
            
            with open('README.md', 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            self.log("📝 README已更新")
            
        except Exception as e:
            self.log(f"写入README文件失败: {e}", "ERROR")


def main():
    """主函数"""
    print("🚀 Weirdhost 自动续期脚本启动")
    print("=" * 50)
    
    login = WeirdhostLogin()
    
    # 检查环境变量
    if not login.has_cookie_auth() and not login.has_email_auth():
        print("❌ 错误：未设置认证信息！")
        print("\n请在 GitHub Secrets 中设置以下任一组合：")
        print("\n方案1 - Cookie 认证：")
        print("WEIRDHOST_COOKIES: pterodactyl_session=你的值; remember_web_59ba36ad=你的值")
        print("\n方案2 - 邮箱密码认证：")
        print("WEIRDHOST_EMAIL: 你的邮箱")
        print("WEIRDHOST_PASSWORD: 你的密码")
        sys.exit(1)
    
    if not login.server_list:
        print("❌ 错误：未设置服务器URL列表！")
        print("\n请在 GitHub Secrets 中设置：")
        print("WEIRDHOST_SERVER_URLS: https://hub.weirdhost.xyz/server/你的服务器ID")
        sys.exit(1)
    
    results = login.run()
    login.write_readme_file(results)
    
    print("=" * 50)
    print("📊 运行结果汇总:")
    for result in results:
        print(f"  - {result}")
    
    if any("login_failed" in result or "error" in result for result in results):
        print("❌ 续期任务有失败的情况！")
        sys.exit(1)
    else:
        print("🎉 续期任务完成！")
        sys.exit(0)


if __name__ == "__main__":
    main()
