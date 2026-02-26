/**
 * 抖音视频字幕提取服务 - v3 (Playwright API拦截版)
 * 
 * 使用 Playwright Python 脚本拦截抖音 API 获取视频信息
 * 解决 yt-dlp 需要 cookies 和页面结构变更的问题
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

// Python 脚本路径 - API拦截版本（优先）
const PYTHON_SCRIPT = path.join(__dirname, '../../scripts/extract-api-intercept.py');
// ASR 兜底脚本（可选）
const ASR_SCRIPT = path.join(__dirname, '../../scripts/asr-fallback.py');

/**
 * 检查依赖是否可用
 */
export async function checkDependencies(useAsr: boolean = false): Promise<{
  python: boolean;
  playwright: boolean;
  script: boolean;
  asrScript?: boolean;
  whisper?: boolean;
  ytDlp?: boolean;
}> {
  const result: any = { python: false, playwright: false, script: false };
  
  try {
    await execFileAsync('python3', ['--version']);
    result.python = true;
  } catch {}
  
  try {
    await execFileAsync('python3', ['-c', 'import playwright']);
    result.playwright = true;
  } catch {}
  
  result.script = fs.existsSync(PYTHON_SCRIPT);
  
  if (useAsr) {
    result.asrScript = fs.existsSync(ASR_SCRIPT);
    try {
      await execFileAsync('python3', ['-c', 'import whisper']);
      result.whisper = true;
    } catch {}
    try {
      await execFileAsync('yt-dlp', ['--version']);
      result.ytDlp = true;
    } catch {}
  }
  
  return result;
}

/**
 * 从抖音分享链接提取视频信息和字幕
 * 
 * 使用 Playwright Python 脚本拦截 API 获取数据
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

  // 检查依赖
  const deps = await checkDependencies();
  if (!deps.python) {
    return { success: false, error: 'Python3 not found', source: 'none' };
  }
  if (!deps.playwright) {
    return { 
      success: false, 
      error: 'Playwright not installed. Run: pip3 install playwright', 
      source: 'none' 
    };
  }
  if (!deps.script) {
    return { success: false, error: 'Extract script not found', source: 'none' };
  }

  try {
    console.log(`[SubtitleExtractor] Extracting: ${shareUrl}`);

    // 执行 Python 脚本
    const { stdout, stderr } = await execFileAsync(
      'python3',
      [PYTHON_SCRIPT, shareUrl],
      { 
        timeout: 60000,
        maxBuffer: 10 * 1024 * 1024,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
      }
    );

    // 解析 Python 脚本输出
    const result = parsePythonOutput(stdout);
    
    if (result.error) {
      return {
        success: false,
        error: result.error,
        source: 'none'
      };
    }

    // 检查是否有字幕
    if (!result.transcript || result.transcript.trim().length === 0) {
      // 尝试 ASR 兜底
      const deps = await checkDependencies(true);
      if (deps.asrScript && deps.whisper && deps.ytDlp) {
        console.log('[SubtitleExtractor] 无自动字幕，尝试 ASR 兜底...');
        const asrResult = await extractWithASR(shareUrl);
        if (asrResult.transcript) {
          return {
            success: true,
            transcript: asrResult.transcript.trim(),
            title: result.title,
            author: result.author,
            duration: result.duration,
            source: 'asr'
          };
        }
      }
      
      return {
        success: false,
        title: result.title,
        author: result.author,
        duration: result.duration,
        error: '该视频没有自动字幕，且 ASR 提取失败',
        source: 'none'
      };
    }

    return {
      success: true,
      transcript: result.transcript.trim(),
      title: result.title,
      author: result.author,
      duration: result.duration,
      source: 'subtitle'
    };

  } catch (error) {
    console.error('[SubtitleExtractor] Error:', error);
    
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    
    if (errorMsg.includes('timeout')) {
      return { success: false, error: '提取超时，请稍后重试', source: 'none' };
    }
    
    return {
      success: false,
      error: `提取失败: ${errorMsg}`,
      source: 'none'
    };
  }
}

/**
 * 解析 Python 脚本输出
 */
function parsePythonOutput(output: string): {
  success?: boolean;
  title?: string;
  author?: string;
  duration?: number;
  transcript?: string;
  transcriptLength?: number;
  error?: string;
} {
  // 提取 JSON 部分
  const jsonStart = output.indexOf('===JSON_START===');
  const jsonEnd = output.indexOf('===JSON_END===');
  
  if (jsonStart !== -1 && jsonEnd !== -1) {
    const jsonStr = output.substring(jsonStart + '===JSON_START==='.length, jsonEnd).trim();
    try {
      return JSON.parse(jsonStr);
    } catch (e) {
      console.error('Failed to parse JSON output:', e);
    }
  }
  
  // 降级：尝试从整段输出解析
  try {
    const lines = output.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        return JSON.parse(trimmed);
      }
    }
  } catch {}
  
  return { error: 'Failed to parse output' };
}

/**
 * 批量提取字幕
 */
export async function batchExtractSubtitles(
  urls: string[],
  concurrency: number = 1
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
      await delay(3000);
    }
  }
  
  return results;
}

/**
 * 使用 ASR 兜底提取
 */
async function extractWithASR(videoUrl: string): Promise<{ transcript?: string; error?: string }> {
  try {
    const { stdout } = await execFileAsync(
      'python3',
      [ASR_SCRIPT, videoUrl],
      {
        timeout: 180000, // ASR 需要更长时间
        maxBuffer: 50 * 1024 * 1024,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
      }
    );

    const result = parsePythonOutput(stdout);
    return {
      transcript: result.transcript,
      error: result.error
    };
  } catch (error) {
    console.error('[ASR] Error:', error);
    return { error: 'ASR 提取失败' };
  }
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 导出测试函数
export async function testExtractor(): Promise<{ available: boolean; message: string }> {
  const deps = await checkDependencies();
  
  if (!deps.python) {
    return { available: false, message: 'Python3 not found' };
  }
  if (!deps.playwright) {
    return { available: false, message: 'Playwright not installed' };
  }
  if (!deps.script) {
    return { available: false, message: 'Extract script not found' };
  }
  
  return { available: true, message: 'All dependencies ready' };
}
