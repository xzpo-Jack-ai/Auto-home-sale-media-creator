#!/usr/bin/env python3
"""
抖音自动登录工具 - 方案 B
功能：启动浏览器显示二维码 → 用户扫码 → 保存 Cookie 供后续使用
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Cookie 保存路径
COOKIE_FILE = Path(__file__).parent / "cookies.json"

def load_saved_cookies():
    """加载已保存的 Cookie"""
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_cookies(cookies):
    """保存 Cookie 到文件"""
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    print(f"✅ Cookie 已保存: {COOKIE_FILE}")

async def auto_login():
    """自动登录流程"""
    print("=" * 70)
    print("🔐 抖音自动登录工具")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查是否有已保存的 Cookie
    saved_cookies = load_saved_cookies()
    if saved_cookies:
        print(f"📂 发现已保存的 Cookie ({len(saved_cookies)} 条)")
        print("   将尝试验证有效性...\n")
    
    async with async_playwright() as p:
        # 启动有界面的浏览器（方便扫码）
        print("🚀 启动浏览器...")
        browser = await p.chromium.launch(
            headless=False,  # 有界面模式，方便扫码
            args=['--window-size=1200,800']
        )
        
        context = await browser.new_context(
            viewport={'width': 1200, 'height': 800}
        )
        
        # 如果有保存的 Cookie，先尝试使用
        if saved_cookies:
            await context.add_cookies(saved_cookies)
            print("📥 已加载保存的 Cookie")
        
        page = await context.new_page()
        
        # 访问抖音创作者平台
        print("\n🌐 正在打开抖音创作者平台...")
        await page.goto('https://creator.douyin.com', wait_until='networkidle')
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 检查当前状态
        current_url = page.url
        print(f"   当前 URL: {current_url}")
        
        # 检查是否已登录
        body_text = await page.evaluate('() => document.body.innerText')
        
        is_logged_in = False
        login_indicators = ['立即登录', '扫码登录', '手机号登录', '登录/注册']
        for indicator in login_indicators:
            if indicator in body_text:
                is_logged_in = False
                break
        else:
            # 检查是否有用户相关元素
            has_user = await page.evaluate('''() => {
                return document.querySelector('[class*="avatar"]') !== null ||
                       document.querySelector('[class*="userName"]') !== null ||
                       document.querySelector('[class*="nickname"]') !== null;
            }''')
            is_logged_in = has_user
        
        if is_logged_in:
            print("\n✅ Cookie 有效，已自动登录！")
            
            # 获取用户信息
            try:
                user_info = await page.evaluate('''() => {
                    const nickEl = document.querySelector('[class*="nickname"]') || 
                                   document.querySelector('[class*="userName"]');
                    return {
                        nickname: nickEl?.textContent?.trim() || '未知用户'
                    };
                }''')
                print(f"   欢迎回来: {user_info['nickname']}")
            except:
                pass
            
            # 保存最新的 Cookie
            cookies = await context.cookies()
            save_cookies(cookies)
            
            print("\n⏳ 5秒后关闭浏览器...")
            await asyncio.sleep(5)
            
        else:
            print("\n⚠️ 需要登录")
            print("   请在浏览器中完成扫码登录\n")
            print("-" * 70)
            print("📱 操作步骤:")
            print("   1. 在打开的浏览器窗口中找到二维码")
            print("   2. 使用抖音 App 扫码")
            print("   3. 确认登录后，按回车键继续...")
            print("-" * 70)
            
            # 等待用户扫码（通过检测 URL 变化或特定元素）
            max_wait = 120  # 最多等待 2 分钟
            waited = 0
            check_interval = 3
            
            while waited < max_wait:
                await asyncio.sleep(check_interval)
                waited += check_interval
                
                # 检查是否已登录
                current_url = page.url
                body_text = await page.evaluate('() => document.body.innerText')
                
                # 如果 URL 变了，或者出现了用户相关元素，说明登录成功
                is_now_logged_in = False
                for indicator in login_indicators:
                    if indicator in body_text:
                        is_now_logged_in = False
                        break
                else:
                    # 检查是否有用户头像或用户名
                    has_user_now = await page.evaluate('''() => {
                        return document.querySelector('[class*="avatar"]') !== null ||
                               document.querySelector('[class*="userName"]') !== null ||
                               document.querySelector('[class*="nickname"]') !== null ||
                               document.querySelector('img[src*="avatar"]') !== null;
                    }''')
                    is_now_logged_in = has_user_now
                
                if is_now_logged_in:
                    print(f"\n✅ 检测到登录成功！({waited}秒)")
                    
                    # 获取用户信息
                    try:
                        user_info = await page.evaluate('''() => {
                            const nickEl = document.querySelector('[class*="nickname"]') || 
                                           document.querySelector('[class*="userName"]') ||
                                           document.querySelector('[class*="name"]');
                            return {
                                nickname: nickEl?.textContent?.trim() || '未知用户'
                            };
                        }''')
                        print(f"   欢迎: {user_info['nickname']}")
                    except:
                        pass
                    
                    # 保存 Cookie
                    cookies = await context.cookies()
                    save_cookies(cookies)
                    
                    print("\n⏳ 3秒后关闭浏览器...")
                    await asyncio.sleep(3)
                    break
                
                # 显示进度
                if waited % 15 == 0:
                    print(f"   等待中... ({waited}/{max_wait}秒)")
            
            else:
                print("\n⏰ 等待超时，未检测到登录")
                print("   你可以手动关闭浏览器窗口")
                await asyncio.sleep(10)
        
        await browser.close()
    
    print("\n" + "=" * 70)
    print("🏁 登录流程结束")
    print("=" * 70)
    
    # 验证保存的 Cookie
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, 'r') as f:
            saved = json.load(f)
        print(f"✅ 已保存 {len(saved)} 条 Cookie")
        print(f"   关键字段:")
        for cookie in saved:
            if cookie['name'] in ['sessionid', 'sessionid_ss', 'sid_tt', 'uid_tt']:
                print(f"     • {cookie['name']}: {cookie['value'][:20]}...")
        return True
    else:
        print("❌ Cookie 保存失败")
        return False


async def verify_cookies():
    """验证已保存的 Cookie 是否有效"""
    print("\n" + "=" * 70)
    print("🔍 验证 Cookie 有效性")
    print("=" * 70)
    
    cookies = load_saved_cookies()
    if not cookies:
        print("❌ 没有找到保存的 Cookie")
        return False
    
    print(f"📂 加载了 {len(cookies)} 条 Cookie")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 访问需要登录的页面
        print("\n🌐 正在测试访问...")
        await page.goto('https://creator.douyin.com/creator-micro/content/manage', 
                       wait_until='networkidle', timeout=30000)
        
        await asyncio.sleep(3)
        
        # 检查登录状态
        body_text = await page.evaluate('() => document.body.innerText')
        current_url = page.url
        
        login_required = any(x in body_text for x in ['登录', '扫码', '请登录'])
        
        if login_required or 'login' in current_url.lower():
            print("❌ Cookie 已过期，需要重新登录")
            await browser.close()
            return False
        else:
            print("✅ Cookie 有效！")
            print(f"   当前页面: {current_url[:60]}...")
            
            # 尝试获取用户名
            try:
                username = await page.evaluate('''() => {
                    const el = document.querySelector('[class*="nickname"]') ||
                              document.querySelector('[class*="userName"]');
                    return el?.textContent?.trim();
                }''')
                if username:
                    print(f"   登录用户: {username}")
            except:
                pass
            
            await browser.close()
            return True


async def main():
    """主函数"""
    import sys
    
    if '--verify' in sys.argv:
        # 只验证 Cookie
        valid = await verify_cookies()
        return 0 if valid else 1
    
    elif '--help' in sys.argv:
        print("""
抖音自动登录工具

用法:
  python auto_login.py          启动登录流程
  python auto_login.py --verify 验证已保存的 Cookie
  python auto_login.py --help   显示帮助

说明:
  1. 首次运行会打开浏览器窗口显示二维码
  2. 使用抖音 App 扫码登录
  3. 登录成功后自动保存 Cookie
  4. 后续抓取脚本会使用保存的 Cookie
        """)
        return 0
    
    else:
        # 执行登录流程
        success = await auto_login()
        return 0 if success else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)
