#!/usr/bin/env python3
"""
增强版抖音视频抓取 - 提取更多字段
包括：播放量、发布时间、视频链接、封面图等
"""

import asyncio
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
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
    author_id: str
    views: int
    likes: int
    shares: int
    comments: int
    video_url: str
    cover_url: str
    duration: int
    published_at: Optional[datetime]
    crawled_at: datetime


class EnhancedVideoCrawler:
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
    
    def _parse_number(self, text: str) -> int:
        """解析数字（支持万、亿等单位）"""
        if not text:
            return 0
        text = str(text).replace(',', '').strip()
        match = re.search(r'(\d+(?:\.\d+)?)\s*[万亿]?', text)
        if match:
            num = float(match.group(1))
            if '万' in text:
                return int(num * 10000)
            elif '亿' in text:
                return int(num * 100000000)
            return int(num)
        return 0
    
    def _parse_time(self, text: str) -> Optional[datetime]:
        """解析时间文本"""
        if not text:
            return None
        
        # 匹配 "2026-02-25" 或 "02-25"
        patterns = [
            (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
            (r'(\d{2}-\d{2})', '%m-%d'),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    if fmt == '%m-%d':
                        date_str = f"2026-{date_str}"
                    return datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    pass
        
        # 处理"X天前"
        day_match = re.search(r'(\d+)\s*天前', text)
        if day_match:
            days = int(day_match.group(1))
            return datetime.now() - timedelta(days=days)
        
        return None
    
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
            for _ in range(3):
                await page.evaluate('window.scrollBy(0, 500)')
                await asyncio.sleep(1)
            
            # 使用JavaScript提取完整的视频信息
            video_data = await page.evaluate('''() => {
                const results = [];
                const seen = new Set();
                
                // 查找所有可能包含视频信息的容器
                const containers = document.querySelectorAll('div[class*="card"], div[class*="item"], [class*="video"]');
                
                for (const container of containers) {
                    // 查找标题（包含#话题标签的长文本）
                    const titleEl = container.querySelector('span, div, h3, h4, a');
                    if (!titleEl) continue;
                    
                    const titleText = titleEl.textContent.trim();
                    
                    // 筛选条件
                    if (titleText.length < 30 || titleText.length > 150 || 
                        !titleText.includes('#') ||
                        titleText.includes('首页') ||
                        titleText.includes('内容管理') ||
                        titleText.includes('数据中心')) {
                        continue;
                    }
                    
                    // 去重
                    if (seen.has(titleText)) continue;
                    seen.add(titleText);
                    
                    // 提取作者
                    let author = '未知作者';
                    const allText = container.textContent;
                    const lines = allText.split('\\n').map(l => l.trim()).filter(l => l);
                    for (const line of lines) {
                        if (line.length > 2 && line.length < 20 && 
                            !line.includes('#') && 
                            !line.includes('发布于') &&
                            !line.match(/^\\d/)) {
                            author = line;
                            break;
                        }
                    }
                    
                    // 提取播放量/热度（查找包含数字和"万"的文本）
                    let views = '';
                    const viewMatch = allText.match(/(\\d+(?:\\.\\d+)?)[万]?[^\\d]*(?:播放|热度|指数)/);
                    if (viewMatch) views = viewMatch[0];
                    
                    // 提取发布时间
                    let publishTime = '';
                    const timeMatch = allText.match(/(\\d{4}-\\d{2}-\\d{2})/);
                    if (timeMatch) publishTime = timeMatch[0];
                    
                    // 提取视频时长（如 03:01）
                    let duration = '';
                    const durationMatch = allText.match(/(\\d{1,2}:\\d{2})/);
                    if (durationMatch) duration = durationMatch[0];
                    
                    // 提取视频链接
                    let videoUrl = '';
                    const linkEl = container.querySelector('a[href*="/video/"], a[href*="/share/"]');
                    if (linkEl) {
                        videoUrl = linkEl.href;
                    }
                    
                    // 提取封面图
                    let coverUrl = '';
                    const imgEl = container.querySelector('img');
                    if (imgEl) {
                        coverUrl = imgEl.src;
                    }
                    
                    results.push({
                        title: titleText,
                        author,
                        views,
                        publishTime,
                        duration,
                        videoUrl,
                        coverUrl
                    });
                    
                    if (results.length >= 10) break;
                }
                
                return results;
            }''')
            
            print(f"   ✅ 提取到 {len(video_data)} 个视频")
            
            for data in video_data:
                # 解析时长（秒）
                duration_sec = 0
                if data.get('duration'):
                    parts = data['duration'].split(':')
                    if len(parts) == 2:
                        duration_sec = int(parts[0]) * 60 + int(parts[1])
                
                videos.append(VideoData(
                    city=city,
                    title=data['title'][:200],
                    author=data['author'][:50],
                    author_id='',
                    views=self._parse_number(data.get('views', '')),
                    likes=0,
                    shares=0,
                    comments=0,
                    video_url=data.get('videoUrl', '')[:500],
                    cover_url=data.get('coverUrl', '')[:500],
                    duration=duration_sec,
                    published_at=self._parse_time(data.get('publishTime', '')),
                    crawled_at=datetime.now()
                ))
                print(f"      ✓ {data['title'][:40]}... | {data.get('author', 'N/A')} | {data.get('views', 'N/A')}")
            
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
            
            saved = 0
            for v in videos:
                external_id = f"enh_{v.city}_{hash(v.title) % 1000000}_{int(datetime.now().timestamp())}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO videos (
                        id, externalId, platform, title, author, authorId,
                        views, likes, shares, comments, coverUrl, videoUrl, duration,
                        transcript, publishedAt, keyword, city, createdAt, updatedAt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    external_id, external_id, 'douyin', v.title, v.author, v.author_id,
                    v.views, v.likes, v.shares, v.comments, v.cover_url, v.video_url, v.duration,
                    '',
                    v.published_at.strftime('%Y-%m-%d %H:%M:%S') if v.published_at else None,
                    f"{v.city}房产", v.city,
                    v.crawled_at.strftime('%Y-%m-%d %H:%M:%S'),
                    v.crawled_at.strftime('%Y-%m-%d %H:%M:%S')
                ))
                saved += 1
            
            conn.commit()
            conn.close()
            print(f"💾 保存 {saved} 条到数据库")
            
        except Exception as e:
            print(f"❌ 数据库错误: {e}")
    
    async def run(self):
        print("=" * 70)
        print("🚀 增强版抖音视频抓取 - 提取更多字段")
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
    crawler = EnhancedVideoCrawler()
    await crawler.run()


if __name__ == '__main__':
    asyncio.run(main())
