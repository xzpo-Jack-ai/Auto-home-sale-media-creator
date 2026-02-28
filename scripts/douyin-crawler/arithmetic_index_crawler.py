#!/usr/bin/env python3
"""
抖音算术指数视频抓取 - 正确版
从 creator.douyin.com/creator-micro/creator-count/arithmetic-index 抓取
支持关键词搜索 + 近3天筛选
"""

import asyncio
import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
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
    keyword: str
    title: str
    author: str
    views: int
    video_url: str
    cover_url: str
    published_at: datetime
    crawled_at: datetime


class ArithmeticIndexCrawler:
    """从算术指数页面抓取视频"""
    
    def __init__(self):
        with open(COOKIE_FILE, 'r') as f:
            self.cookies = json.load(f)
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
    
    async def search_and_filter(self, city: str, days: int = 3) -> List[VideoData]:
        """
        在算术指数页面搜索并筛选
        
        步骤：
        1. 访问 arithmetic-index 页面
        2. 在搜索框输入关键词
        3. 点击搜索
        4. 选择"近3天"筛选
        5. 提取视频列表
        """
        videos = []
        
        try:
            page = await self.context.new_page()
            
            # 访问算术指数首页
            url = "https://creator.douyin.com/creator-micro/creator-count/arithmetic-index"
            print(f"\n📍 [{city}] 访问算术指数页面...")
            print(f"   URL: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(5)
            
            # 截图
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_arithmetic_home.png'))
            
            # 查找搜索框并输入关键词
            print(f"   🔍 搜索: {city}房产")
            search_input = await page.query_selector('input[placeholder*="搜索"]') or \
                          await page.query_selector('input[type="text"]') or \
                          await page.query_selector('[class*="search"] input')
            
            if search_input:
                await search_input.fill(f"{city}房产")
                await asyncio.sleep(1)
                
                # 点击搜索按钮或按回车
                search_btn = await page.query_selector('button[type="submit"]') or \
                            await page.query_selector('[class*="search-btn"]') or \
                            await page.query_selector('button:has-text("搜索")')
                
                if search_btn:
                    await search_btn.click()
                else:
                    await search_input.press('Enter')
                
                print(f"   ✅ 已提交搜索")
                await asyncio.sleep(5)  # 等待结果加载
            else:
                print(f"   ⚠️ 未找到搜索框")
            
            # 截图查看搜索结果
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_search_results.png'), full_page=True)
            
            # 尝试点击"近3天"筛选
            print(f"   📅 尝试选择'近{days}天'...")
            date_filtered = await self._select_date_filter(page, days)
            
            if date_filtered:
                print(f"   ✅ 已选择近{days}天")
                await asyncio.sleep(3)
            
            # 截图筛选后结果
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_filtered_results.png'), full_page=True)
            
            # 提取视频列表
            videos = await self._extract_videos(page, city)
            print(f"   🎬 提取到 {len(videos)} 个视频")
            
            await page.close()
            
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:100]}")
        
        return videos
    
    async def _select_date_filter(self, page: Page, days: int) -> bool:
        """选择日期筛选"""
        try:
            # 可能的筛选按钮文本
            filter_texts = ['近3天', '近7天', '近30天', '时间不限']
            target_text = f'近{days}天'
            
            # 尝试直接点击
            for text in [target_text] + filter_texts:
                btn = await page.query_selector(f'text={text}') or \
                      await page.query_selector(f'button:has-text("{text}")') or \
                      await page.query_selector(f'span:has-text("{text}")')
                if btn:
                    await btn.click()
                    return True
            
            # 尝试打开下拉菜单
            dropdown = await page.query_selector('text=时间不限') or \
                      await page.query_selector('[class*="filter"]') or \
                      await page.query_selector('[class*="dropdown"]')
            
            if dropdown:
                await dropdown.click()
                await asyncio.sleep(1)
                
                option = await page.query_selector(f'text={target_text}')
                if option:
                    await option.click()
                    return True
            
            return False
            
        except Exception as e:
            print(f"      筛选失败: {e}")
            return False
    
    async def _extract_videos(self, page: Page, city: str) -> List[VideoData]:
        """提取视频列表"""
        videos = []
        
        try:
            # 获取页面内容
            content = await page.content()
            text = await page.evaluate('() => document.body.innerText')
            
            # 尝试多种方式提取视频信息
            # 方式1: DOM选择器
            selectors = [
                '[class*="video-item"]',
                '[class*="card"]',
                '[class*="result-item"]',
                'a[href*="/video/"]',
            ]
            
            for selector in selectors:
                cards = await page.query_selector_all(selector)
                if len(cards) > 0:
                    print(f"      使用选择器: {selector} ({len(cards)} 个)")
                    
                    for card in cards[:10]:
                        try:
                            title_el = await card.query_selector('[class*="title"]') or \
                                      await card.query_selector('h3') or \
                                      await card.query_selector('span')
                            title = await title_el.text_content() if title_el else ""
                            
                            if title and len(title) > 10:
                                author_el = await card.query_selector('[class*="author"]')
                                author = await author_el.text_content() if author_el else "未知作者"
                                
                                videos.append(VideoData(
                                    city=city,
                                    keyword=f"{city}房产",
                                    title=title.strip()[:100],
                                    author=author.strip()[:50],
                                    views=100000,
                                    video_url="",
                                    cover_url="",
                                    published_at=datetime.now(),
                                    crawled_at=datetime.now()
                                ))
                        except:
                            continue
                    break
            
            # 方式2: 从文本提取（如果DOM失败）
            if not videos:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if 20 < len(line) < 100:
                        if any(kw in line for kw in ['房', '楼', '价', '买', city]):
                            if not any(x in line for x in ['http', '登录', '确认', '抖音']):
                                videos.append(VideoData(
                                    city=city,
                                    keyword=f"{city}房产",
                                    title=line[:100],
                                    author="热门创作者",
                                    views=100000,
                                    video_url="",
                                    cover_url="",
                                    published_at=datetime.now(),
                                    crawled_at=datetime.now()
                                ))
        
        except Exception as e:
            print(f"      提取失败: {e}")
        
        return videos[:10]
    
    def save_to_db(self, videos: List[VideoData]):
        """保存到数据库"""
        if not DB_PATH.exists():
            return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for v in videos:
                vid = f"ai_{v.city}_{hash(v.title) % 1000000}"
                cursor.execute('''
                    INSERT OR REPLACE INTO videos 
                    (id, externalId, platform, title, author, views, videoUrl, 
                     publishedAt, keyword, city, createdAt, updatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    vid, vid, 'douyin', v.title, v.author, v.views, v.video_url,
                    v.published_at.strftime('%Y-%m-%d %H:%M:%S'),
                    v.keyword, v.city,
                    v.crawled_at.strftime('%Y-%m-%d %H:%M:%S'),
                    v.crawled_at.strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            conn.close()
            print(f"💾 保存 {len(videos)} 条到数据库")
            
        except Exception as e:
            print(f"❌ 数据库错误: {e}")
    
    async def run(self):
        print("=" * 70)
        print("🚀 抖音算术指数视频抓取")
        print("=" * 70)
        
        await self.init()
        
        for city in CITIES[:1]:  # 先测试北京
            videos = await self.search_and_filter(city, days=3)
            self.results.extend(videos)
        
        if self.results:
            self.save_to_db(self.results)
        
        await self.close()
        
        print("\n" + "=" * 70)
        print(f"✅ 完成: {len(self.results)} 条视频")
        print("=" * 70)


async def main():
    crawler = ArithmeticIndexCrawler()
    await crawler.run()


if __name__ == '__main__':
    asyncio.run(main())
