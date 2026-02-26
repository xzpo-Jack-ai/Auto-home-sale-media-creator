/**
 * 抖音视频字幕提取服务 - v2 (yt-dlp 版本)
 * 
 * 使用 yt-dlp 工具提取抖音视频信息和字幕
 * yt-dlp 自动处理抖音的签名验证和反爬机制
 * 
 * @author ShadowJack
 * @date 2026-02-26
 */

import { execFile } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';

const execFileAsync = promisify(execFile);

export interface SubtitleResult {
  success: boolean;
  transcript?: string;
  title?: string;
  author?: string;
  duration?: number;
  source: 'subtitle' | 'asr' | 'none';
  error?: string;
}

interface YtDlpVideoInfo {
  id: string;
  title: string;
  description?: string;
  duration?: number;
  uploader?: string;
  uploader_id?: string;
  subtitles?: Record<string, Array<{
    url: string;
    name: string;
  }>>;
  automatic_captions?: Record<string, Array<{
    url: string;
    name: string;
  }>>;
  webpage_url?: string;
  original_url?: string;
}

// yt-dlp 路径
const YT_DLP_PATH = '/opt/homebrew/bin/yt-dlp';

// cookies 文件路径
const COOKIES_PATH = path.join(__dirname, '../../cookies/douyin.txt');

/**
 * 检查 yt-dlp 是否可用
 */
async function checkYtDlp(): Promise<boolean> {
  try {
    await execFileAsync(YT_DLP_PATH, ['--version']);
    return true;
  } catch {
    // 尝试备用路径
    try {
      await execFileAsync('yt-dlp', ['--version']);
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * 获取 yt-dlp 可执行路径
 */
async function getYtDlpPath(): Promise<string | null> {
  const paths = [YT_DLP_PATH, 'yt-dlp', '/usr/local/bin/yt-dlp'];
  for (const p of paths) {
    try {
      await execFileAsync(p, ['--version']);
      return p;
    } catch {
      continue;
    }
  }
  return null;
}

/**
 * 从抖音分享链接提取视频信息和字幕
 * 
 * 使用 yt-dlp 提取：
 * 1. 视频元数据（标题、作者、时长）
 * 2. 自动字幕（如果可用）
 * 
 * @param shareUrl - 抖音分享链接
 * @returns SubtitleResult
 */
export async function extractDouyinSubtitle(shareUrl: string): Promise<SubtitleResult> {
  // 输入验证
  if (!shareUrl || typeof shareUrl !== 'string') {
    return { success: false, error: 'Invalid input: shareUrl must be a non-empty string', source: 'none' };
  }

  if (!shareUrl.startsWith('http://') && !shareUrl.startsWith('https://')) {
    return { success: false, error: 'Invalid URL format', source: 'none' };
  }

  const ytDlpPath = await getYtDlpPath();
  if (!ytDlpPath) {
    return { success: false, error: 'yt-dlp not found. Please install: pip install yt-dlp', source: 'none' };
  }

  try {
    console.log(`[SubtitleExtractor] Using yt-dlp: ${ytDlpPath}`);
    console.log(`[SubtitleExtractor] Extracting: ${shareUrl}`);

    // 检查 cookies 文件是否存在
    const hasCookies = fs.existsSync(COOKIES_PATH);
    if (hasCookies) {
      console.log(`[SubtitleExtractor] Using cookies: ${COOKIES_PATH}`);
    }

    // 步骤1: 获取视频信息
    const args = [
      '--dump-json',
      '--no-download',
      '--quiet',
      '--skip-download',
      '--no-warnings',
      '--add-header', 'Referer:https://www.douyin.com/',
      '--add-header', 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    ];
    
    if (hasCookies) {
      args.push('--cookies', COOKIES_PATH);
    }
    
    args.push(shareUrl);

    const { stdout: infoJson } = await execFileAsync(
      ytDlpPath,
      args,
      { timeout: 30000, maxBuffer: 10 * 1024 * 1024 } // 30秒超时，10MB缓冲
    );

    const videoInfo: YtDlpVideoInfo = JSON.parse(infoJson);
    console.log(`[SubtitleExtractor] Video ID: ${videoInfo.id}`);
    console.log(`[SubtitleExtractor] Title: ${videoInfo.title?.substring(0, 50)}...`);
    console.log(`[SubtitleExtractor] Duration: ${videoInfo.duration}s`);

    // 步骤2: 尝试获取字幕
    let transcript: string | undefined;
    let source: 'subtitle' | 'asr' | 'none' = 'none';

    // 优先获取自动生成的字幕（抖音通常是自动字幕）
    const autoCaptions = videoInfo.automatic_captions || videoInfo.subtitles;
    
    if (autoCaptions) {
      console.log(`[SubtitleExtractor] Available captions:`, Object.keys(autoCaptions));
      
      // 优先选择中文简体
      const langPriority = ['zh-CN', 'zh', 'zh-Hans', 'zh-TW', 'zh-Hant'];
      let selectedLang: string | null = null;
      
      for (const lang of langPriority) {
        if (autoCaptions[lang] && autoCaptions[lang].length > 0) {
          selectedLang = lang;
          break;
        }
      }

      // 如果没有中文，使用第一个可用语言
      if (!selectedLang) {
        selectedLang = Object.keys(autoCaptions)[0];
      }

      if (selectedLang) {
        console.log(`[SubtitleExtractor] Selected language: ${selectedLang}`);
        
        // 获取字幕内容（优先 JSON3 格式，通常包含完整时间戳）
        const formats = autoCaptions[selectedLang];
        const jsonFormat = formats.find(f => f.name?.includes('json') || f.url?.includes('json'));
        const targetFormat = jsonFormat || formats[0];

        if (targetFormat) {
          try {
            transcript = await fetchSubtitleContent(targetFormat.url);
            if (transcript) source = 'subtitle';
          } catch (err) {
            console.error(`[SubtitleExtractor] Failed to fetch subtitle:`, err);
          }
        }
      }
    }

    if (!transcript) {
      return {
        success: false,
        title: videoInfo.title,
        author: videoInfo.uploader,
        duration: videoInfo.duration,
        error: '该视频没有自动字幕',
        source: 'none'
      };
    }

    return {
      success: true,
      transcript: transcript.trim(),
      title: videoInfo.title,
      author: videoInfo.uploader,
      duration: videoInfo.duration,
      source
    };

  } catch (error) {
    console.error('[SubtitleExtractor] Error:', error);
    
    // 解析 yt-dlp 错误信息
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    
    if (errorMsg.includes('Video unavailable')) {
      return { success: false, error: '视频不可用或链接已失效', source: 'none' };
    }
    if (errorMsg.includes('Private video')) {
      return { success: false, error: '该视频是私密视频', source: 'none' };
    }
    if (errorMsg.includes('Sign in') || errorMsg.includes('cookies')) {
      return { 
        success: false, 
        error: '抖音需要登录才能提取。请从浏览器导出 cookies 保存到 cookies/douyin.txt', 
        source: 'none' 
      };
    }
    if (errorMsg.includes('timeout')) {
      return { success: false, error: '提取超时，请稍后重试', source: 'none' };
    }
    if (errorMsg.includes('parse JSON') || errorMsg.includes('Forbidden')) {
      return { 
        success: false, 
        error: '抖音反爬机制阻止了提取。请配置 cookies 文件', 
        source: 'none' 
      };
    }
    
    return {
      success: false,
      error: `提取失败: ${errorMsg}`,
      source: 'none'
    };
  }
}

/**
 * 获取字幕内容
 */
async function fetchSubtitleContent(url: string): Promise<string | undefined> {
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': '*/*',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const contentType = response.headers.get('content-type') || '';
    
    if (contentType.includes('json')) {
      const data = await response.json();
      return parseJsonSubtitle(data);
    }
    
    // SRT 格式
    const text = await response.text();
    return parseSrt(text);
    
  } catch (error) {
    console.error('Fetch subtitle error:', error);
    return undefined;
  }
}

/**
 * 解析 JSON 字幕格式
 */
function parseJsonSubtitle(data: any): string {
  if (Array.isArray(data)) {
    // YouTube/抖音 JSON 格式
    return data
      .filter((item: any) => item.text || item.content)
      .map((item: any) => (item.text || item.content).trim())
      .join('\n');
  }
  
  if (data.events || data.utterances) {
    // 其他 JSON 格式
    const items = data.events || data.utterances;
    return items
      .filter((item: any) => item.segs || item.text)
      .map((item: any) => {
        if (item.segs) {
          return item.segs.map((seg: any) => seg.utf8 || '').join('');
        }
        return item.text || '';
      })
      .join('\n');
  }
  
  return '';
}

/**
 * 解析 SRT 字幕格式
 */
function parseSrt(srtContent: string): string {
  const lines = srtContent.split('\n');
  const texts: string[] = [];
  let isTextLine = false;

  for (const line of lines) {
    const trimmed = line.trim();
    
    // 跳过序号和时间轴行
    if (/^\d+$/.test(trimmed)) {
      isTextLine = false;
      continue;
    }
    if (/\d{2}:\d{2}:\d{2}[,.]\d{3}/.test(trimmed)) {
      isTextLine = true;
      continue;
    }
    if (trimmed === '') {
      isTextLine = false;
      continue;
    }
    
    if (isTextLine && trimmed) {
      texts.push(trimmed);
    }
  }

  return texts.join('\n');
}

/**
 * 批量提取字幕
 */
export async function batchExtractSubtitles(
  urls: string[],
  concurrency: number = 2
): Promise<SubtitleResult[]> {
  const results: SubtitleResult[] = [];
  
  for (let i = 0; i < urls.length; i += concurrency) {
    const batch = urls.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(url => extractDouyinSubtitle(url))
    );
    results.push(...batchResults);
    
    // 添加延迟避免触发风控
    if (i + concurrency < urls.length) {
      await delay(2000 + Math.random() * 1000);
    }
  }
  
  return results;
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 导出测试函数
export async function testYtDlp(): Promise<{ available: boolean; version?: string }> {
  try {
    const ytDlpPath = await getYtDlpPath();
    if (!ytDlpPath) return { available: false };
    
    const { stdout } = await execFileAsync(ytDlpPath, ['--version']);
    return { available: true, version: stdout.trim() };
  } catch {
    return { available: false };
  }
}
