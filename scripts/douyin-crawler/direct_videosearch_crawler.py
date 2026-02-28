#!/usr/bin/env python3
"""
直接访问视频搜索URL
根据用户提供的截图，使用正确的URL格式
"""

import asyncio
import json
import re
import sqlite3
from datetime import datetime, timedelta
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


class DirectVideoSearchCrawler:
    """直接访问视频搜索URL"""
    
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
    
    async def search_videos(self, city: str) -> List[VideoData]:
        """直接访问视频搜索URL"""
        videos = []
        
        try:
            page = await self.context.new_page()
            
            # 使用用户提供的URL格式
            query = f"{city},房产"
            url = f"https://creator.douyin.com/creator-micro/creator-count/arithmetic-index/videosearch?query={quote(query)}&source=creator&page=1"
            
            print(f"\n📍 [{city}] 直接访问视频搜索URL...")
            print(f"   URL: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(5)
            
            # 截图
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_videosearch.png'), full_page=True)
            print(f"   📸 已截图")
            
            # 检查是否被重定向
            current_url = page.url
            print(f"   当前URL: {current_url[:80]}...")
            
            if 'videosearch' not in current_url:
                print(f"   ⚠️ 被重定向到: {current_url}")
                print(f"   可能需要特定权限或入口")
            else:
                print(f"   ✅ 成功访问视频搜索页面")
                
                # 关闭升级提示弹窗
                print(f"   关闭弹窗...")
                try:
                    confirm_btn = await page.wait_for_selector('button:has-text("确认")', timeout=5000)
                    if confirm_btn:
                        await confirm_btn.click()
                        await asyncio.sleep(2)
                        print(f"      ✅ 已关闭弹窗")
                except:
                    pass
                
                # 选择近3天筛选
                print(f"   尝试选择'近3天'...")
                try:
                    date_btn = await page.wait_for_selector('text=近3天', timeout=5000)
                    if date_btn:
                        await date_btn.click()
                        await asyncio.sleep(3)
                        print(f"      ✅ 已选择近3天")
                except:
                    print(f"      ⚠️ 未找到近3天按钮")
                
                # 再次截图（关闭弹窗后）
                await page.screenshot(path=str(OUTPUT_DIR / f'{city}_videosearch_clean.png'), full_page=True)
                
                # 提取视频
                videos = await self._extract_videos(page, city)
            
            await page.close()
            
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:100]}")
        
        return videos
    
    async def _extract_videos(self, page: Page, city: str) -> List[VideoData]:
        """从视频搜索页提取视频"""
        videos = []
        
        try:
            # 滚动页面确保所有内容加载
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(2)
            
            # 使用JavaScript提取视频信息（更可靠）
            video_data = await page.evaluate('''() => {
                const results = [];
                
                // 方法1: 查找所有包含视频信息的div（根据截图结构）
                // 视频卡片通常包含图片、标题、作者信息
                const allDivs = document.querySelectorAll('div');
                
                for (const div of allDivs) {
                    // 查找包含标题的元素（h3或长文本span/div）
                    const titleEl = div.querySelector('h3, h4');
                    if (!titleEl) continue;
                    
                    const title = titleEl.textContent.trim();
                    if (!title || title.length < 20) continue;
                    
                    // 查找作者（通常在标题下方）
                    let author = '未知作者';
                    const nextEl = titleEl.parentElement;
                    if (nextEl) {
                        const authorEl = nextEl.querySelector('span, div');
                        if (authorEl && authorEl.textContent.length < 50) {
                            author = authorEl.textContent.trim();
                        }
                    }
                    
                    // 查找播放量（包含数字和"万"的文本）
                    let views = '0';
                    const text = div.textContent;
                    const viewMatch = text.match(/(\d+(?:\.\d+)?)[万]?/);
                    if (viewMatch) views = viewMatch[0];
                    
                    // 查找时间（发布于XXXX-XX-XX）
                    let time = '';
                    const timeMatch = text.match(/(\d{4}-\d{2}-\d{2})/);
                    if (timeMatch) time = timeMatch[0];
                    
                    // 去重检查
                    if (!results.find(r => r.title === title)) {
                        results.push({title, author, views, time});
                    }
                    
                    if (results.length >= 10) break;
                }
                
                return results;
            }''')
            
            print(f"   JavaScript提取到 {len(video_data)} 个视频")
            
            for data in video_data[:10]:
                videos.append(VideoData(
                    city=city,
                    title=data['title'][:100],
                    author=data['author'][:50],
                    views=self._parse_views(data['views']),
                    video_url="",
                    published_at=self._parse_time(data['time'])
                ))
                print(f"      ✓ {data['title'][:40]}...")
        
        except Exception as e:
            print(f"   提取失败: {e}")
        
        return videos
    
    def _parse_views(self, text: str) -> int:
        if not text:
            return 0
        match = re.search(r'(\d+(?:\.\d+)?)[万]?', text)
        if match:
            num = float(match.group(1))
            return int(num * 10000) if '万' in text else int(num)
        return 0
    
    def _parse_time(self, text: str) -> datetime:
        # 解析时间文本
        if not text:
            return datetime.now()
        
        # 匹配 "2026-02-25" 或 "02-25"
        match = re.search(r'(\d{4}-)?(\d{2}-\d{2})', text)
        if match:
            date_str = match.group(0)
            if not match.group(1):  # 没有年份
                date_str = f"2026-{date_str}"
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except:
                pass
        
        return datetime.now()
    
    def save_to_db(self, videos: List[VideoData]):
        if not DB_PATH.exists() or not videos:
            return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for v in videos:
                vid = f"vs_{v.city}_{hash(v.title) % 1000000}"
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
        print("🚀 直接访问视频搜索URL")
        print("=" * 70)
        
        await self.init()
        
        for city in CITIES[:2]:  # 先测试2个城市
            videos = await self.search_videos(city)
            self.results.extend(videos)
            await asyncio.sleep(5)
        
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
    crawler = DirectVideoSearchCrawler()
    await crawler.run()


if __name__ == '__main__':
    asyncio.run(main())
