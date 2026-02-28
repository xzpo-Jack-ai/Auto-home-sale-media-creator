#!/usr/bin/env python3
"""
抖音登录工具 - 简化版
直接显示二维码页面，扫码后保存 Cookie
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path(__file__).parent / "cookies.json"

async def simple_login():
    """简化登录流程"""
    print("=" * 60)
    print("🔐 抖音扫码登录")
    print("=" * 60)
    print()
    
    async with async_playwright() as p:
        # 启动有界面浏览器
        browser = await p.chromium.launch(
            headless=False,
            args=['--window-size=1000,800']
        )
        
        context = await browser.new_context(viewport={'width': 1000, 'height': 800})
        page = await context.new_page()
        
        print("🌐 正在打开登录页面...")
        
        try:
            # 访问巨量算数（通常不需要登录也能看到部分数据）
            await page.goto('https://trendinsight.oceanengine.com', timeout=60000)
        except:
            pass
        
        print("\n📱 请完成以下操作：")
        print("   1. 在浏览器窗口中找到登录/扫码入口")
        print("   2. 点击登录按钮")
        print("   3. 使用抖音 App 扫描二维码")
        print("   4. 在手机上确认登录")
        print("   5. 回到这里按回车键继续...")
        print()
        print("⏳ 等待登录完成（2分钟超时）...")
        print("-" * 60)
        
        # 等待用户操作
        logged_in = False
        for i in range(24):  # 2分钟 = 24 * 5秒
            await asyncio.sleep(5)
            
            # 检查当前 URL 和页面内容
            try:
                url = page.url
                title = await page.title()
                
                # 如果 URL 包含个人中心或管理页面，说明已登录
                if any(x in url for x in ['/manage', '/personal', '/home']):
                    logged_in = True
                    break
                
                # 检查页面是否有用户相关元素
                has_user = await page.evaluate('''() => {
                    const text = document.body.innerText;
                    return !text.includes('登录') && !text.includes('扫码');
                }''')
                
                if has_user and i > 6:  # 至少等待30秒
                    logged_in = True
                    break
                
                if i % 6 == 0 and i > 0:
                    print(f"   等待中... ({i*5}秒)")
                    
            except Exception as e:
                print(f"   检查状态出错: {e}")
        
        if logged_in:
            print("\n✅ 检测到登录成功！")
            
            # 获取并保存 Cookie
            cookies = await context.cookies()
            
            with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Cookie 已保存: {COOKIE_FILE}")
            print(f"   共 {len(cookies)} 条")
            
            # 显示关键 Cookie
            for c in cookies:
                if c['name'] in ['sessionid', 'sessionid_ss', 'uid_tt']:
                    print(f"   • {c['name']}: {c['value'][:25]}...")
            
            print("\n⏳ 3秒后关闭浏览器...")
            await asyncio.sleep(3)
            
        else:
            print("\n⏰ 等待超时")
            print("   如果你已完成登录，Cookie 可能已保存")
            
            # 尝试保存即使可能未登录
            try:
                cookies = await context.cookies()
                if len(cookies) > 5:
                    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)
                    print(f"💾 已保存 {len(cookies)} 条 Cookie")
            except:
                pass
            
            print("\n按回车键关闭浏览器...")
            await asyncio.sleep(5)
        
        await browser.close()
    
    print("\n" + "=" * 60)
    print("🏁 登录流程结束")
    print("=" * 60)
    
    # 验证结果
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, 'r') as f:
            data = json.load(f)
        print(f"✅ Cookie 文件存在: {len(data)} 条")
        return True
    else:
        print("❌ Cookie 文件未生成")
        return False


if __name__ == '__main__':
    success = asyncio.run(simple_login())
    exit(0 if success else 1)
