#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weirdhost 登录页面调试脚本 - 详细分析页面结构
"""

import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

class WeirdhostDebug:
    def __init__(self):
        self.email = os.getenv('WEIRDHOST_EMAIL', '')
        self.password = os.getenv('WEIRDHOST_PASSWORD', '')
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def run_debug(self):
        """运行详细的调试分析"""
        self.log("🚀 开始 Weirdhost 登录页面调试分析")
        
        with sync_playwright() as p:
            # 启动浏览器（显示界面以便观察）
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                # 1. 访问登录页面
                self.log("1. 访问登录页面...")
                page.goto('https://hub.weirdhost.xyz/auth/login', wait_until='networkidle')
                time.sleep(3)
                
                # 2. 获取基本页面信息
                self.log("2. 获取页面基本信息:")
                self.log(f"   - 页面标题: {page.title()}")
                self.log(f"   - 当前URL: {page.url}")
                
                # 3. 分析所有输入框
                self.log("3. 分析所有输入框:")
                inputs = page.locator('input')
                input_count = inputs.count()
                self.log(f"   找到 {input_count} 个输入框:")
                
                for i in range(input_count):
                    input_elem = inputs.nth(i)
                    input_info = {
                        'index': i,
                        'type': input_elem.get_attribute('type') or '无type',
                        'name': input_elem.get_attribute('name') or '无name',
                        'id': input_elem.get_attribute('id') or '无id',
                        'placeholder': input_elem.get_attribute('placeholder') or '无placeholder',
                        'class': input_elem.get_attribute('class') or '无class'
                    }
                    self.log(f"     输入框 {i}: {input_info}")
                
                # 4. 分析所有按钮
                self.log("4. 分析所有按钮:")
                buttons = page.locator('button, input[type="submit"]')
                button_count = buttons.count()
                self.log(f"   找到 {button_count} 个按钮:")
                
                for i in range(button_count):
                    button_elem = buttons.nth(i)
                    button_info = {
                        'index': i,
                        'type': button_elem.get_attribute('type') or 'button',
                        'text': (button_elem.text_content() or '无文本').strip(),
                        'class': button_elem.get_attribute('class') or '无class'
                    }
                    self.log(f"     按钮 {i}: {button_info}")
                
                # 5. 分析表单
                self.log("5. 分析表单:")
                forms = page.locator('form')
                form_count = forms.count()
                self.log(f"   找到 {form_count} 个表单:")
                
                for i in range(form_count):
                    form = forms.nth(i)
                    form_info = {
                        'index': i,
                        'action': form.get_attribute('action') or '无action',
                        'method': form.get_attribute('method') or '无method',
                        'class': form.get_attribute('class') or '无class'
                    }
                    self.log(f"     表单 {i}: {form_info}")
                
                # 6. 测试常见的选择器
                self.log("6. 测试常见的选择器:")
                
                # 测试邮箱选择器
                email_selectors = [
                    'input[name="username"]',
                    'input[name="email"]',
                    'input[type="email"]',
                    'input[type="text"]:first-of-type',
                    'input:first-of-type',
                    'form input:first-of-type'
                ]
                
                self.log("   邮箱输入框选择器测试:")
                for selector in email_selectors:
                    elements = page.locator(selector)
                    count = elements.count()
                    if count > 0:
                        self.log(f"     ✅ '{selector}' - 找到 {count} 个元素")
                    else:
                        self.log(f"     ❌ '{selector}' - 未找到元素")
                
                # 测试密码选择器
                password_selectors = [
                    'input[name="password"]',
                    'input[type="password"]',
                    'input[type="password"]:last-of-type',
                    'input:last-of-type',
                    'form input:last-of-type'
                ]
                
                self.log("   密码输入框选择器测试:")
                for selector in password_selectors:
                    elements = page.locator(selector)
                    count = elements.count()
                    if count > 0:
                        self.log(f"     ✅ '{selector}' - 找到 {count} 个元素")
                    else:
                        self.log(f"     ❌ '{selector}' - 未找到元素")
                
                # 7. 保存页面HTML用于分析
                html_content = page.content()
                with open('login_page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.log("7. 已保存页面HTML到: login_page_debug.html")
                
                # 8. 保存截图
                page.screenshot(path='login_page_debug.png')
                self.log("8. 已保存页面截图到: login_page_debug.png")
                
                self.log("✅ 调试分析完成！")
                self.log("请查看上面的输出结果，找到正确的选择器")
                
                # 暂停以便查看结果
                input("按回车键关闭浏览器...")
                
            except Exception as e:
                self.log(f"❌ 调试过程中出错: {e}")
            finally:
                browser.close()

def main():
    debug = WeirdhostDebug()
    debug.run_debug()

if __name__ == "__main__":
    main()
