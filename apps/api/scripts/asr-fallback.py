#!/usr/bin/env python3
"""
抖音视频字幕提取 - ASR 兜底方案 (简化版)

流程:
1. 用 yt-dlp 下载视频音频
2. 用 Whisper ASR 转写

依赖:
- pip install openai-whisper
- brew install ffmpeg yt-dlp
"""

import subprocess
import tempfile
import os
import sys
import json

class DouyinASR:
    def __init__(self):
        self.cookies_path = "/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/cookies/douyin.txt"
    
    def extract(self, video_url: str) -> dict:
        """提取视频音频并使用 ASR 转写"""
        result = {
            'url': video_url,
            'transcript': None,
            'source': None,
            'error': None
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, 'audio.m4a')
            
            # 步骤1: 用 yt-dlp 下载音频
            print("⬇️  下载音频...")
            try:
                cmd = [
                    'yt-dlp',
                    '-f', 'ba',  # best audio
                    '-o', audio_path,
                    '--cookies-from-browser', 'chrome',  # 从 Chrome 浏览器获取 cookies
                    '--no-warnings',
                    '-q',
                    video_url
                ]
                subprocess.run(cmd, check=True, capture_output=True, timeout=60)
                
                # yt-dlp 会自动添加扩展名
                for ext in ['.m4a', '.mp4', '.webm', '.mp3']:
                    if os.path.exists(audio_path + ext):
                        audio_path = audio_path + ext
                        break
                
                file_size = os.path.getsize(audio_path)
                print(f"✅ 音频已下载: {file_size} bytes")
                
                if file_size < 10000:
                    result['error'] = '音频文件太小，下载可能失败'
                    return result
                    
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                if 'cookies' in error_msg.lower() or 'sign' in error_msg.lower():
                    result['error'] = 'Cookies 失效，需要重新获取'
                else:
                    result['error'] = f'下载失败: {error_msg[:100]}'
                return result
            except Exception as e:
                result['error'] = f'下载失败: {e}'
                return result
            
            # 步骤2: Whisper ASR 转写
            print("🎙️  Whisper ASR 转写中...")
            try:
                import whisper
                
                model = whisper.load_model('base')
                
                # 转写
                asr_result = model.transcribe(audio_path, language='zh', fp16=False, verbose=False)
                
                result['transcript'] = asr_result.get('text', '').strip()
                result['source'] = 'asr'
                
                print(f"✅ ASR 完成: {len(result['transcript'])} 字符")
                
            except Exception as e:
                result['error'] = f'ASR 失败: {e}'
                return result
        
        return result


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/od9jc8Ju4t8/"
    
    extractor = DouyinASR()
    result = extractor.extract(url)
    
    output = {
        "success": bool(result.get('transcript')),
        **result
    }
    
    print("\n===JSON_START===")
    print(json.dumps(output, ensure_ascii=False))
    print("===JSON_END===")


if __name__ == "__main__":
    main()
