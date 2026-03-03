#!/usr/bin/env python3
"""
上海视频批量ASR处理
从数据库读取上海视频，提取音频文案
"""

import sqlite3
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")
DASHSCOPE_SCRIPT = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/scripts/douyin-audio-asr.py")
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_shanghai_videos_without_transcript():
    """获取上海且没有文案的视频"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, externalId, videoUrl, title, author, likes
        FROM videos
        WHERE city = '上海' AND (transcript IS NULL OR transcript = '') AND videoUrl LIKE '%douyin%'
        ORDER BY likes DESC
        LIMIT 5
    ''')
    
    videos = []
    for row in cursor.fetchall():
        videos.append({
            'id': row[0],
            'externalId': row[1],
            'videoUrl': row[2],
            'title': row[3],
            'author': row[4],
            'likes': row[5]
        })
    
    conn.close()
    return videos


def extract_asr(video_url: str) -> str:
    """使用DashScope ASR提取文案"""
    try:
        print(f"      🎙️ ASR识别中...")
        result = subprocess.run(
            ['python3', str(DASHSCOPE_SCRIPT), video_url],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout
        
        # 方法1: 查找 "📝 结果:" 后面的内容
        if '📝 结果:' in output:
            idx = output.find('📝 结果:')
            if idx != -1:
                result_text = output[idx + 6:].strip()
                # 取第一行（实际文案）
                lines = [l.strip() for l in result_text.split('\n') if l.strip()]
                if lines:
                    return lines[0]
        
        # 方法2: 查找 "转写成功!" 后的内容
        if '转写成功!' in output:
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if '转写成功!' in line or '📝 结果:' in line:
                    # 取接下来的非空行
                    for j in range(i+1, min(i+5, len(lines))):
                        if lines[j].strip() and not lines[j].startswith('费用:'):
                            return lines[j].strip()
        
        return ""
    except Exception as e:
        print(f"      ❌ ASR失败: {e}")
        return ""


def update_transcript(video_id: str, transcript: str):
    """更新数据库中的文案"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE videos SET transcript = ?, updatedAt = ? WHERE id = ?
    ''', (transcript[:2000], datetime.now().isoformat(), video_id))
    
    conn.commit()
    conn.close()


def main():
    print("=" * 70)
    print("🎙️ 上海视频批量ASR处理")
    print("=" * 70)
    
    # 获取待处理的视频
    videos = get_shanghai_videos_without_transcript()
    print(f"\n📊 找到 {len(videos)} 条待处理视频\n")
    
    results = []
    
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video['author']}")
        print(f"   点赞: {video['likes']} | 标题: {video['title'][:50]}...")
        
        # ASR提取
        transcript = extract_asr(video['videoUrl'])
        
        if transcript:
            print(f"   ✅ 文案 ({len(transcript)}字): {transcript[:100]}...")
            
            # 更新数据库
            update_transcript(video['id'], transcript)
            
            results.append({
                'id': video['id'],
                'author': video['author'],
                'title': video['title'],
                'transcript': transcript,
                'likes': video['likes']
            })
        else:
            print(f"   ⚠️ 未提取到文案")
        
        print()
    
    # 保存报告
    report_file = OUTPUT_DIR / f"shanghai_asr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("=" * 70)
    print(f"✅ 完成! 成功处理 {len(results)}/{len(videos)} 条视频")
    print(f"📊 报告: {report_file}")
    print("=" * 70)


if __name__ == '__main__':
    main()
