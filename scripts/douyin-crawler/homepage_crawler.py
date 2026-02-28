#!/usr/bin/env python3
"""
从创作者中心首页抓取热门视频
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path(__file__).parent / "cookies.json"
OUTPUT_DIR = Path(__file__).parent / "output"

async def crawl_homepage():
    with open(COOKIE_FILE, 'r') as f:
        cookies = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1400, 'height': 900})
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 访问首页
        print("访问创作者中心首页...")
        await page.goto('https://creator.douyin.com', wait_until='networkidle')
        await asyncio.sleep(5)
        
        # 截图
        await page.screenshot(path=str(OUTPUT_DIR / 'homepage_full.png'), full_page=True)
        print("已截图保存")
        
        # 提取热门视频
        videos = await page.evaluate('''() => {
            const results = [];
            // 查找所有视频卡片
            const cards = document.querySelectorAll('[class*="video"], [class*="card"], [class*="item"]');
            cards.forEach(card => {
                const title = card.querySelector('[class*="title"], h3, h4, span')?.textContent?.trim();
                const author = card.querySelector('[class*="author"], [class*="name"]')?.textContent?.trim();
                const heat = card.querySelector('[class*="heat"], [class*="hot"]')?.textContent?.trim();
                if (title && title.length > 10) {
                    results.push({title, author, heat});
                }
            });
            return results;
        }''')
        
        print(f"\n找到 {len(videos)} 个视频:")
        for i, v in enumerate(videos[:10]):
            print(f"{i+1}. {v.get('title', 'N/A')[:50]}...")
            print(f"   作者: {v.get('author', 'N/A')}")
            print(f"   热度: {v.get('heat', 'N/A')}")
        
        await browser.close()

asyncio.run(crawl_homepage())
