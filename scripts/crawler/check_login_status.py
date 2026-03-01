#!/usr/bin/env python3
"""
检查抖音创作者平台登录状态
访问指定URL并截图，查看是否需要登录
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path(__file__).parent / "cookies.json"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

async def check_login():
    """检查登录状态"""
    print("=" * 60)
    print("🔍 抖音创作者平台登录状态检查")
    print("=" * 60)
    
    # 目标URL - 杭州房产视频搜索
    url = "https://creator.douyin.com/creator-micro/creator-count/arithmetic-index/videosearch?query=%E6%9D%AD%E5%B7%9E%E6%88%BF%E4%BA%A7&source=creator"
    
    async with async_playwright() as p:
        # 启动有界面浏览器便于观察
        browser = await p.chromium.launch(
            headless=False,
            args=['--window-size=1400,900']
        )
        
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        # 尝试加载cookie（如果存在）
        if COOKIE_FILE.exists():
            with open(COOKIE_FILE, 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print(f"✅ 已加载 {len(cookies)} 条 Cookie")
        else:
            print("⚠️ 未找到 Cookie 文件")
        
        page = await context.new_page()
        
        print(f"\n🌐 正在访问: {url[:80]}...")
        response = await page.goto(url, wait_until='networkidle', timeout=60000)
        
        print(f"📊 响应状态: {response.status}")
        print(f"📍 最终URL: {page.url[:80]}...")
        
        # 等待页面加载
        await asyncio.sleep(5)
        
        # 获取页面文本内容
        page_text = await page.evaluate('() => document.body.innerText')
        
        # 检查是否需要登录
        login_indicators = ['登录', '扫码', '立即登录', '手机号登录', '验证码']
        needs_login = any(indicator in page_text for indicator in login_indicators)
        
        # 检查是否有用户相关元素
        has_user_info = await page.evaluate('''() => {
            const text = document.body.innerText;
            return text.includes('创作者中心') && 
                   (document.querySelector('[class*="avatar"]') !== null ||
                    document.querySelector('[class*="user-name"]') !== null ||
                    text.includes('退出'));
        }''')
        
        print("\n" + "-" * 60)
        if needs_login:
            print("❌ 需要登录")
            print("\n页面包含以下登录提示:")
            for indicator in login_indicators:
                if indicator in page_text:
                    print(f"   • {indicator}")
        elif has_user_info:
            print("✅ 已登录")
        else:
            print("⚠️ 状态不明")
        
        # 显示页面内容预览
        print("\n📄 页面内容预览:")
        preview = page_text[:500].replace('\n', ' ')
        print(f"   {preview}...")
        
        # 截图保存
        screenshot_path = OUTPUT_DIR / "login_check.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n📸 截图已保存: {screenshot_path}")
        
        # 如果已登录，尝试提取视频信息
        if not needs_login:
            print("\n🔍 尝试提取视频信息...")
            videos = await page.evaluate('''() => {
                const results = [];
                // 尝试多种选择器查找视频
                const selectors = [
                    '[data-e2e="video-item"]',
                    '[class*="video-card"]',
                    '[class*="search-result"]'
                ];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        console.log(`找到 ${elements.length} 个元素: ${selector}`);
                        for (let i = 0; i < Math.min(elements.length, 5); i++) {
                            const el = elements[i];
                            const title = el.querySelector('[class*="title"]')?.textContent?.trim() || '';
                            if (title) results.push(title);
                        }
                        break;
                    }
                }
                return results;
            }''')
            
            if videos:
                print(f"\n🎬 找到 {len(videos)} 个视频:")
                for i, title in enumerate(videos[:5], 1):
                    print(f"   {i}. {title[:60]}...")
            else:
                print("⚠️ 未找到视频列表")
        
        print("\n" + "=" * 60)
        print("检查完成")
        print("=" * 60)
        
        # 保持浏览器打开以便用户查看
        print("\n⏳ 浏览器将保持打开 30 秒...")
        print("   请查看页面状态，完成后关闭浏览器窗口")
        await asyncio.sleep(30)
        
        await browser.close()
        
        return not needs_login

if __name__ == '__main__':
    success = asyncio.run(check_login())
    exit(0 if success else 1)
