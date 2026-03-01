#!/usr/bin/env python3
"""
抖音 Cookie 获取工具
自动打开浏览器让用户扫码登录，然后导出 Cookie
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "cookies.json"

async def get_cookies():
    """获取抖音登录 Cookie"""
    print("=" * 60)
    print("🔐 抖音 Cookie 获取工具")
    print("=" * 60)
    print("\n即将打开浏览器，请按以下步骤操作：")
    print("1. 使用抖音 App 扫描二维码登录")
    print("2. 登录成功后，关闭浏览器窗口")
    print("3. Cookie 将自动保存到 cookies.json\n")
    print("-" * 60)
    
    async with async_playwright() as p:
        # 启动有界面浏览器
        browser = await p.chromium.launch(
            headless=False,
            args=['--window-size=1400,900']
        )
        
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        
        page = await context.new_page()
        
        # 访问创作者平台
        print("🌐 正在打开 creator.douyin.com...")
        await page.goto('https://creator.douyin.com', wait_until='networkidle')
        
        # 等待用户登录（通过检查页面元素）
        print("⏳ 等待登录...")
        print("   请在浏览器中完成扫码登录")
        
        # 循环检查登录状态
        max_wait = 300  # 最多等待5分钟
        for i in range(max_wait):
            await asyncio.sleep(1)
            
            # 检查是否已登录
            try:
                current_url = page.url
                
                # 如果 URL 不包含 login，可能已登录成功
                if 'login' not in current_url.lower():
                    # 进一步检查是否有用户相关元素
                    has_user = await page.evaluate('''() => {
                        return document.querySelector('[class*="avatar"]') !== null ||
                               document.querySelector('[class*="user-name"]') !== null ||
                               document.body.innerText.includes('创作者中心');
                    }''')
                    
                    if has_user:
                        print(f"\n✅ 检测到登录成功！")
                        break
                
                # 每30秒提醒一次
                if (i + 1) % 30 == 0:
                    print(f"   已等待 {(i+1)} 秒，请完成登录...")
                    
            except Exception as e:
                pass
        else:
            print("\n⚠️ 等待超时，请重新运行脚本")
            await browser.close()
            return False
        
        # 获取 Cookie
        print("\n📥 正在获取 Cookie...")
        cookies = await context.cookies()
        
        # 筛选 douyin.com 相关的 cookie
        douyin_cookies = [
            {
                'name': c['name'],
                'value': c['value'],
                'domain': c['domain'],
                'path': c['path'],
                **({'expires': c['expires']} if c.get('expires') else {}),
                **({'secure': c['secure']} if c.get('secure') else {}),
            }
            for c in cookies
            if 'douyin' in c.get('domain', '') or 'iesdouyin' in c.get('domain', '')
        ]
        
        # 保存到文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(douyin_cookies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cookie 已保存: {OUTPUT_FILE}")
        print(f"   共 {len(douyin_cookies)} 条 Cookie")
        
        # 显示关键 Cookie
        key_cookies = ['sessionid', 'sid_tt', 'passport_csrf_token', 'ttwid']
        print("\n🔑 关键 Cookie:")
        for c in douyin_cookies:
            if any(key in c['name'] for key in key_cookies):
                value_preview = c['value'][:30] + '...' if len(c['value']) > 30 else c['value']
                print(f"   {c['name']}: {value_preview}")
        
        # 验证登录状态
        print("\n🧪 验证登录状态...")
        await page.goto('https://creator.douyin.com/creator-micro/content/manage', wait_until='networkidle')
        await asyncio.sleep(2)
        
        is_logged_in = await page.evaluate('''() => {
            return !document.body.innerText.includes('登录') &&
                   !document.body.innerText.includes('扫码');
        }''')
        
        if is_logged_in:
            print("✅ 登录状态验证通过！")
        else:
            print("⚠️ 可能需要重新登录")
        
        await browser.close()
        return True


if __name__ == '__main__':
    success = asyncio.run(get_cookies())
    exit(0 if success else 1)
