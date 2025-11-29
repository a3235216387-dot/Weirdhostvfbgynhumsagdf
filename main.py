#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weirdhost 自动续期脚本 - 修复选择器版本
"""

import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

class WeirdhostAutoRenew:
    def __init__(self):
        # 认证信息
        self.cookies_str = os.getenv('WEIRDHOST_COOKIES', '')
        self.email = os.getenv('WEIRDHOST_EMAIL', '')
        self.password = os.getenv('WEIRDHOST_PASSWORD', '')
        self.server_url = os.getenv('WEIRDHOST_SERVER_URLS', 'https://hub.weirdhost.xyz/server/db60dafc')
        
        # 解析 Cookie
        self.cookies_dict = {}
        if self.cookies_str:
            for cookie in self.cookies_str.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    self.cookies_dict[key] = value
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def check_login_status(self, page):
        """检查登录状态"""
        try:
            page_content = page.content().lower()
            current_url = page.url.lower()
            
            # 如果 URL 或内容包含登录相关关键词，说明未登录
            login_indicators = ['login', 'auth', 'sign in', 'username', 'password']
            if any(indicator in current_url for indicator in login_indicators) or \
               any(indicator in page_content for indicator in login_indicators):
                return False
            return True
        except:
            return False
    
    def login_with_cookies(self, context):
        """使用 Cookie 登录"""
        if not self.cookies_dict:
            return False
            
        try:
            cookies_to_add = []
            for name, value in self.cookies_dict.items():
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': '.weirdhost.xyz',
                    'path': '/',
                }
                cookies_to_add.append(cookie)
            
            context.add_cookies(cookies_to_add)
            self.log(f"✅ 已添加 {len(cookies_to_add)} 个 Cookie")
            return True
        except Exception as e:
            self.log(f"❌ Cookie 登录失败: {e}")
            return False
    
    def login_with_email(self, page):
        """使用邮箱密码登录 - 修复选择器版本"""
        try:
            self.log("尝试邮箱密码登录...")
            
            # 访问登录页面
            page.goto('https://hub.weirdhost.xyz/auth/login', wait_until='networkidle')
            time.sleep(3)
            
            # 尝试多种可能的选择器
            email_selectors = [
                'input[name="username"]',      # 最常见
                'input[name="email"]',         # 可能使用 email
                'input[type="text"]',          # 通用文本输入
                'input[placeholder*="email" i]',  # 包含 email 的 placeholder
                'input[placeholder*="user" i]',   # 包含 user 的 placeholder
            ]
            
            password_selectors = [
                'input[name="password"]',      # 最常见
                'input[type="password"]',      # 密码类型
            ]
            
            submit_selectors = [
                'button[type="submit"]',       # 提交按钮
                'button:has-text("Login")',    # 包含 Login 的按钮
                'button:has-text("登录")',      # 包含 登录 的按钮
                'button:has-text("Sign In")',  # 包含 Sign In 的按钮
            ]
            
            # 查找邮箱/用户名输入框
            email_field = None
            for selector in email_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        email_field = page.locator(selector)
                        self.log(f"找到邮箱输入框: {selector}")
                        break
                except:
                    continue
            
            if not email_field:
                self.log("❌ 未找到邮箱输入框")
                # 截图用于调试
                page.screenshot(path="debug_login_form.png")
                self.log("已保存登录页面截图: debug_login_form.png")
                return False
            
            # 查找密码输入框
            password_field = None
            for selector in password_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        password_field = page.locator(selector)
                        self.log(f"找到密码输入框: {selector}")
                        break
                except:
                    continue
            
            if not password_field:
                self.log("❌ 未找到密码输入框")
                return False
            
            # 查找提交按钮
            submit_button = None
            for selector in submit_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        submit_button = page.locator(selector)
                        self.log(f"找到提交按钮: {selector}")
                        break
                except:
                    continue
            
            if not submit_button:
                self.log("❌ 未找到提交按钮")
                return False
            
            # 填写登录信息
            self.log("填写登录信息...")
            email_field.fill(self.email)
            password_field.fill(self.password)
            
            # 点击登录按钮
            self.log("点击登录按钮...")
            submit_button.click()
            
            # 等待登录完成
            page.wait_for_timeout(5000)
            
            # 检查是否登录成功
            if self.check_login_status(page):
                self.log("✅ 邮箱密码登录成功")
                return True
            else:
                self.log("❌ 邮箱密码登录失败")
                # 检查是否有错误信息
                error_indicators = ['error', 'invalid', 'incorrect', 'wrong']
                page_content = page.content().lower()
                if any(indicator in page_content for indicator in error_indicators):
                    self.log("页面显示错误信息，可能是账号密码错误")
                return False
                
        except Exception as e:
            self.log(f"❌ 邮箱密码登录出错: {e}")
            # 截图用于调试
            try:
                page.screenshot(path="login_error.png")
                self.log("已保存错误截图: login_error.png")
            except:
                pass
            return False
    
    def renew_server(self, page):
        """续期服务器"""
        try:
            self.log(f"访问服务器页面: {self.server_url}")
            page.goto(self.server_url, wait_until='networkidle')
            time.sleep(3)
            
            # 检查是否已登录
            if not self.check_login_status(page):
                self.log("❌ 访问服务器页面时未登录")
                return False
            
            # 查找续期按钮
            button_selectors = [
                'button:has-text("시간추가")',
                'button:has-text("시간 추가")',
                '//button[contains(text(), "시간추가")]',
                '//button[contains(text(), "시간 추가")]',
            ]
            
            for selector in button_selectors:
                try:
                    if selector.startswith('//'):
                        button = page.locator(f'xpath={selector}')
                    else:
                        button = page.locator(selector)
                    
                    if button.count() > 0 and button.first.is_visible():
                        self.log(f"✅ 找到续期按钮: {selector}")
                        
                        if button.first.is_enabled():
                            button.first.click()
                            time.sleep(5)
                            self.log("✅ 已点击续期按钮")
                            return True
                        else:
                            self.log("❌ 续期按钮不可点击")
                            return False
                except:
                    continue
            
            self.log("❌ 未找到续期按钮")
            # 保存页面截图用于调试
            page.screenshot(path="debug_server_page.png")
            self.log("已保存服务器页面截图: debug_server_page.png")
            return False
            
        except Exception as e:
            self.log(f"❌ 续期过程中出错: {e}")
            return False
    
    def run(self):
        """主运行函数"""
        self.log("开始 Weirdhost 自动续期任务")
        
        # 检查认证信息
        has_cookie = bool(self.cookies_dict)
        has_email = bool(self.email and self.password)
        
        self.log(f"Cookie 认证: {has_cookie}, 邮箱密码认证: {has_email}")
        
        if not has_cookie and not has_email:
            self.log("❌ 没有可用的认证信息")
            return False
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                login_success = False
                
                # 首先尝试 Cookie 登录
                if has_cookie and self.login_with_cookies(context):
                    page.goto('https://hub.weirdhost.xyz/', wait_until='networkidle')
                    time.sleep(3)
                    if self.check_login_status(page):
                        login_success = True
                        self.log("✅ Cookie 登录成功")
                    else:
                        self.log("❌ Cookie 登录失败")
                
                # 如果 Cookie 登录失败，尝试邮箱密码登录
                if not login_success and has_email:
                    if self.login_with_email(page):
                        login_success = True
                
                # 如果登录成功，执行续期
                if login_success:
                    return self.renew_server(page)
                else:
                    self.log("❌ 所有登录方式都失败")
                    return False
                    
            finally:
                browser.close()

def main():
    print("🚀 Weirdhost 自动续期脚本启动")
    print("=" * 50)
    
    renewer = WeirdhostAutoRenew()
    success = renewer.run()
    
    print("=" * 50)
    if success:
        print("✅ 续期任务完成！")
        exit(0)
    else:
        print("❌ 续期任务失败！")
        exit(1)

if __name__ == "__main__":
    main()
