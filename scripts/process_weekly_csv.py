#!/usr/bin/env python3
"""
每周CSV视频数据处理流程
1. 读取CSV（城市、链接、标题）
2. 提取视频信息（ASR获取完整文案）
3. AI分析标题总结热词
4. 将视频归类到热词下
"""

import asyncio
import csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 配置
DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ASR脚本路径
API_INTERCEPT_SCRIPT = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/scripts/extract-api-intercept.py")
DASHSCOPE_ASR_SCRIPT = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/scripts/douyin-audio-asr.py")


class WeeklyCSVProcessor:
    """每周CSV处理器"""
    
    def __init__(self):
        self.videos: List[Dict] = []
        self.hot_keywords: Dict[str, List[Dict]] = {}  # 热词 -> 视频列表
    
    def read_csv(self, csv_file: str) -> List[Dict]:
        """读取CSV文件"""
        print(f"📖 读取CSV: {csv_file}")
        
        videos = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                videos.append({
                    'city': row.get('city', '').strip(),
                    'video_url': row.get('video_url', '').strip(),
                    'title': row.get('title', '').strip(),
                    'raw_data': row
                })
        
        print(f"   ✅ 读取 {len(videos)} 条记录")
        return videos
    
    async def extract_video_info(self, video: Dict) -> Dict:
        """提取视频信息（标题、文案）"""
        import subprocess
        import re
        
        url = video['video_url']
        print(f"   🔍 提取: {url[:50]}...")
        
        # 如果CSV中已有标题，直接使用
        if video.get('title'):
            print(f"      📌 使用CSV中的标题: {video['title'][:40]}...")
            video['extracted_title'] = video['title']
        else:
            # 尝试API拦截获取标题
            try:
                result = subprocess.run(
                    ['python3', str(API_INTERCEPT_SCRIPT), url],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # 解析输出
                json_match = re.search(r'===JSON_START===(.+?)===JSON_END===', result.stdout, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                    video['extracted_title'] = data.get('title', '')
                    video['transcript'] = data.get('transcript', '')
                else:
                    video['extracted_title'] = ''
            except Exception as e:
                print(f"      ⚠️ API拦截失败: {e}")
                video['extracted_title'] = ''
        
        # 如果没有文案，尝试ASR
        if not video.get('transcript'):
            try:
                print(f"      🎙️ ASR提取文案...")
                result = subprocess.run(
                    ['python3', str(DASHSCOPE_ASR_SCRIPT), url],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                # 查找转写结果
                for line in result.stdout.split('\n'):
                    if '转写文本:' in line:
                        video['transcript'] = line.split('转写文本:', 1)[1].strip()
                        break
            except Exception as e:
                print(f"      ⚠️ ASR失败: {e}")
                video['transcript'] = ''
        
        return video
    
    async def analyze_hot_keywords(self, videos: List[Dict]) -> Dict[str, List[Dict]]:
        """使用AI分析热词并归类视频"""
        print("\n🔥 分析热词...")
        
        # 导入AI分析器
        from ai_hot_keyword_analyzer import AIHotKeywordAnalyzer, Video
        
        # 转换为Video对象
        video_objects = [
            Video(
                city=v['city'],
                title=v.get('extracted_title', '') or v.get('title', ''),
                url=v['video_url'],
                transcript=v.get('transcript', '')
            )
            for v in videos
        ]
        
        # AI分析
        analyzer = AIHotKeywordAnalyzer()
        hot_keywords = await analyzer.analyze_with_fallback(video_objects)
        
        # 转换回字典格式
        keyword_map = {}
        for kw in hot_keywords:
            keyword_key = f"{kw.videos[0].city if kw.videos else '未知'}-{kw.keyword}"
            keyword_map[keyword_key] = [
                {
                    'city': v.city,
                    'title': v.title,
                    'video_url': v.url,
                    'transcript': v.transcript,
                    'heat_score': kw.heat_score,
                    'category': kw.category
                }
                for v in kw.videos
            ]
        
        print(f"   ✅ AI发现 {len(keyword_map)} 个热词")
        for kw, vids in sorted(keyword_map.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            heat = vids[0].get('heat_score', 50) if vids else 50
            cat = vids[0].get('category', '其他') if vids else '其他'
            print(f"      • {kw} (热度:{heat}, {cat}): {len(vids)} 个视频")
        
        return keyword_map
    
    def save_to_database(self, videos: List[Dict], hot_keywords: Dict):
        """保存到数据库"""
        if not DB_PATH.exists():
            print(f"⚠️ 数据库不存在: {DB_PATH}")
            return False
        
        print("\n💾 保存到数据库...")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            saved_videos = 0
            saved_keywords = 0
            
            # 1. 保存视频
            for video in videos:
                external_id = f"dy_{video['city']}_{hash(video['video_url']) % 1000000}_{int(datetime.now().timestamp())}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO videos (
                        id, externalId, platform, title, author, 
                        views, likes, shares, comments, videoUrl,
                        duration, transcript, keyword, city, createdAt, updatedAt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    external_id,
                    external_id,
                    'douyin',
                    video.get('extracted_title', '')[:150],
                    video.get('author', ''),
                    video.get('views', 0),
                    video.get('likes', 0),
                    video.get('shares', 0),
                    video.get('comments', 0),
                    video['video_url'],
                    video.get('duration', 0),
                    video.get('transcript', '')[:2000],
                    video.get('keyword', ''),
                    video['city'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                saved_videos += 1
            
            # 2. 保存热词
            for keyword, vids in hot_keywords.items():
                parts = keyword.split('-', 1)
                city = parts[0] if len(parts) > 0 else '未知'
                keyword_text = parts[1] if len(parts) > 1 else keyword
                
                cursor.execute('''
                    INSERT INTO Keyword (city, text, heat, updatedAt)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(city, text) DO UPDATE SET
                        heat = excluded.heat,
                        updatedAt = excluded.updatedAt
                ''', (
                    city,
                    keyword_text,
                    len(vids) * 10,  # 热度 = 视频数 * 10
                    datetime.now().isoformat()
                ))
                saved_keywords += 1
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ 保存 {saved_videos} 个视频")
            print(f"   ✅ 保存 {saved_keywords} 个热词")
            return True
            
        except Exception as e:
            print(f"❌ 数据库错误: {e}")
            return False
    
    def generate_report(self, videos: List[Dict], hot_keywords: Dict, output_file: str):
        """生成处理报告"""
        report = {
            'date': datetime.now().isoformat(),
            'total_videos': len(videos),
            'total_keywords': len(hot_keywords),
            'hot_keywords': [
                {
                    'keyword': kw,
                    'video_count': len(vids),
                    'videos': [
                        {
                            'city': v['city'],
                            'title': v.get('extracted_title', '')[:50],
                            'url': v['video_url']
                        }
                        for v in vids[:5]  # 每个热词最多显示5个
                    ]
                }
                for kw, vids in list(hot_keywords.items())[:20]  # 最多20个热词
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 报告已生成: {output_file}")
    
    async def process(self, csv_file: str):
        """主处理流程"""
        print("=" * 70)
        print("📅 每周CSV视频数据处理")
        print("=" * 70)
        
        # 1. 读取CSV
        videos = self.read_csv(csv_file)
        
        # 2. 提取视频信息
        print("\n🎬 提取视频信息...")
        for i, video in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}]")
            await self.extract_video_info(video)
        
        # 3. 分析热词
        hot_keywords = self.analyze_hot_keywords(videos)
        
        # 4. 保存到数据库
        self.save_to_database(videos, hot_keywords)
        
        # 5. 生成报告
        report_file = OUTPUT_DIR / f"weekly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.generate_report(videos, hot_keywords, str(report_file))
        
        print("\n" + "=" * 70)
        print("✅ 处理完成")
        print("=" * 70)
        print(f"总视频数: {len(videos)}")
        print(f"热词数: {len(hot_keywords)}")
        print(f"报告: {report_file}")


async def main():
    if len(sys.argv) < 2:
        print("用法: python3 process_weekly_csv.py <csv文件>")
        print("\nCSV格式示例:")
        print("city,video_url,title")
        print("北京,https://v.douyin.com/xxxxx,北京学区房攻略")
        print("上海,https://v.douyin.com/yyyyy,上海新房开盘")
        sys.exit(1)
    
    processor = WeeklyCSVProcessor()
    await processor.process(sys.argv[1])


if __name__ == '__main__':
    asyncio.run(main())
