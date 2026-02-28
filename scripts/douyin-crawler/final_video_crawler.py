#!/usr/bin/env python3
"""
最终版抖音视频抓取 - 基于实际DOM结构
"""

import asyncio
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List
from urllib.parse import quote
from playwright.async_api import async_playwright, Page

COOKIE_FILE = Path(__file__).parent / "cookies.json"
DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CITIES = ['北京', '上海', '深圳', '广州', '杭州', '成都']

@dataclass
class VideoData:
    city: str
    title: str
    author: str
    views: int
    video_url: str
    published_at: datetime


class FinalVideoCrawler:
    def __init__(self):
        self.cookies = json.load(open(COOKIE_FILE))
        self.results: List[VideoData] = []
    
    async def init(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        await self.context.add_cookies(self.cookies)
        print("✅ 浏览器初始化完成")
    
    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()
    
    async def crawl_city(self, city: str) -> List[VideoData]:
        """抓取单个城市"""
        videos = []
        
        try:
            page = await self.context.new_page()
            
            # 直接访问视频搜索URL
            query = f"{city},房产"
            url = f"https://creator.douyin.com/creator-micro/creator-count/arithmetic-index/videosearch?query={quote(query)}&source=creator&page=1"
            
            print(f"\n📍 [{city}] 访问视频搜索...")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(5)
            
            # 关闭弹窗
            try:
                btn = await page.wait_for_selector('button:has-text("确认")', timeout=3000)
                if btn:
                    await btn.click()
                    await asyncio.sleep(2)
                    print(f"   ✅ 已关闭弹窗")
            except:
                pass
            
            # 滚动加载更多内容
            await page.evaluate('window.scrollBy(0, 800)')
            await asyncio.sleep(2)
            
            # 使用JavaScript提取视频信息（基于实际发现的DOM结构）
            video_data = await page.evaluate('''() => {
                const results = [];
                const seen = new Set();
                
                // 查找所有span和div元素
                const elements = document.querySelectorAll('span, div');
                
                for (const el of elements) {
                    const text = el.textContent.trim();
                    
                    // 筛选条件：长度30-100，包含#话题标签，不包含导航菜单文字
                    if (text.length >= 30 && text.length <= 100 && 
                        text.includes('#') && 
                        !text.includes('首页') &&
                        !text.includes('内容管理') &&
                        !text.includes('数据中心') &&
                        !text.includes('创作中心')) {
                        
                        // 去重
                        if (!seen.has(text)) {
                            seen.add(text);
                            
                            // 尝试找到作者（父元素中的短文本）
                            let author = '未知作者';
                            const parent = el.parentElement;
                            if (parent) {
                                const siblings = parent.querySelectorAll('span, div');
                                for (const sib of siblings) {
                                    const sibText = sib.textContent.trim();
                                    if (sibText.length > 2 && sibText.length < 20 && 
                                        sibText !== text &&
                                        !sibText.includes('#')) {
                                        author = sibText;
                                        break;
                                    }
                                }
                            }
                            
                            results.push({title: text, author});
                        }
                    }
                    
                    if (results.length >= 10) break;
                }
                
                return results;
            }''')
            
            print(f"   ✅ 提取到 {len(video_data)} 个视频")
            
            for data in video_data:
                videos.append(VideoData(
                    city=city,
                    title=data['title'][:100],
                    author=data['author'][:50],
                    views=100000,  # 默认值
                    video_url="",
                    published_at=datetime.now()
                ))
                print(f"      ✓ {data['title'][:50]}...")
            
            await page.close()
            
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:80]}")
        
        return videos
    
    def save_to_db(self, videos: List[VideoData]):
        if not DB_PATH.exists() or not videos:
            return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for v in videos:
                vid = f"final_{v.city}_{hash(v.title) % 1000000}_{int(datetime.now().timestamp())}"
                cursor.execute('''
                    INSERT OR REPLACE INTO videos 
                    (id, externalId, platform, title, author, views, 
                     publishedAt, keyword, city, createdAt, updatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    vid, vid, 'douyin', v.title, v.author, v.views,
                    v.published_at.strftime('%Y-%m-%d %H:%M:%S'),
                    f"{v.city}房产", v.city,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            conn.close()
            print(f"💾 保存 {len(videos)} 条到数据库")
            
        except Exception as e:
            print(f"❌ 数据库错误: {e}")
    
    async def run(self):
        print("=" * 70)
        print("🚀 最终版抖音视频抓取")
        print("=" * 70)
        
        await self.init()
        
        for city in CITIES[:2]:  # 先测试2个城市
            videos = await self.crawl_city(city)
            self.results.extend(videos)
            await asyncio.sleep(3)
        
        if self.results:
            self.save_to_db(self.results)
        
        await self.close()
        
        print("\n" + "=" * 70)
        print(f"✅ 完成: {len(self.results)} 条视频")
        for city in CITIES[:2]:
            count = sum(1 for v in self.results if v.city == city)
            print(f"   {city}: {count} 条")
        print("=" * 70)


async def main():
    crawler = FinalVideoCrawler()
    await crawler.run()


if __name__ == '__main__':
    asyncio.run(main())
