#!/usr/bin/env python3
"""
将ASR结果导入数据库
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")
ASR_FILE = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/scripts/output/shanghai_asr_20260303_200050.json")


def import_asr():
    print("=" * 70)
    print("📥 导入ASR文案到数据库")
    print("=" * 70)
    
    # 读取ASR结果
    with open(ASR_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    print(f"\n📊 ASR文件包含 {len(videos)} 条视频")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated = 0
    for video in videos:
        video_id = video.get('id')
        transcript = video.get('transcript', '')
        
        if not video_id or not transcript:
            continue
        
        # 更新数据库
        cursor.execute('''
            UPDATE videos 
            SET transcript = ?, updatedAt = ?
            WHERE id = ?
        ''', (transcript, datetime.now().isoformat(), video_id))
        
        if cursor.rowcount > 0:
            updated += 1
            print(f"✅ 更新: {video.get('author', 'Unknown')} - {transcript[:50]}...")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 成功更新 {updated} 条视频的文案")


if __name__ == '__main__':
    import_asr()
