#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie 测试脚本 - 验证 Weirdhost Cookie 是否有效
"""

import os
import requests
from datetime import datetime

def log(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")

def test_cookies():
    """测试 Cookie 是否有效"""
    
    # 从环境变量获取 Cookie
    cookies_str = os.getenv('WEIRDHOST_COOKIES', '')
    log(f"原始 Cookie 字符串: {cookies_str}")
    
    if not cookies_str:
        log("❌ 未找到 WEIRDHOST_COOKIES 环境变量", "ERROR")
        return False
    
    # 解析 Cookie
    cookies = {}
    for cookie in cookies_str.split(';'):
        cookie = cookie.strip()
        if '=' in cookie:
            key, value = cookie.split('=', 1)
            cookies[key] = value
            log(f"解析到 Cookie: {key} = {value[:20]}...")
    
    if not cookies:
        log("❌ 无法解析 Cookie", "ERROR")
        return False
    
    # 创建会话并设置 Cookie
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # 添加 Cookie 到会话
    for key, value in cookies.items():
        session.cookies.set(key, value, domain='.weirdhost.xyz')
    
    # 测试访问服务器页面
    test_url = "https://hub.weirdhost.xyz/server/db60dafc"
    log(f"测试访问: {test_url}")
    
    try:
        response = session.get(test_url, timeout=10)
        log(f"HTTP 状态码: {response.status_code}")
        
        # 检查响应内容判断登录状态
        if response.status_code == 200:
            content = response.text.lower()
            
            # 检查是否包含登录相关关键词
            login_indicators = ['login', 'sign in', '登录', 'email', 'password']
            if any(indicator in content for indicator in login_indicators):
                log("❌ Cookie 无效 - 重定向到登录页面")
                return False
            else:
                log("✅ Cookie 有效 - 成功访问服务器页面")
                
                # 检查是否找到续期按钮
                if '시간추가' in response.text or '시간 추가' in response.text:
                    log("✅ 找到续期按钮")
                    return True
                else:
                    log("⚠️  Cookie 有效但未找到续期按钮")
                    return True
        else:
            log(f"❌ HTTP 错误: {response.status_code}")
            return False
            
    except Exception as e:
        log(f"❌ 请求失败: {e}", "ERROR")
        return False

if __name__ == "__main__":
    print("🔍 Weirdhost Cookie 测试工具")
    print("=" * 50)
    
    success = test_cookies()
    
    print("=" * 50)
    if success:
        print("✅ Cookie 测试通过！")
    else:
        print("❌ Cookie 测试失败！")
        print("\n请检查：")
        print("1. WEIRDHOST_COOKIES 环境变量是否正确设置")
        print("2. Cookie 是否已过期")
        print("3. 服务器URL是否正确")
