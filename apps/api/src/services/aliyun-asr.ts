/**
 * 阿里云语音识别服务 (ASR)
 * 
 * 使用阿里云语音转写服务进行视频音频识别
 * 支持: 视频URL输入，自动转写为文本
 * 
 * 文档: https://help.aliyun.com/document_detail/90780.html
 * 
 * @author ShadowJack
 * @date 2026-02-26
 */

// 阿里云语音识别服务

// 阿里云配置
const ALIYUN_CONFIG = {
  accessKeyId: process.env.ALIYUN_ACCESS_KEY_ID || '',
  accessKeySecret: process.env.ALIYUN_ACCESS_KEY_SECRET || '',
  appKey: process.env.ALIYUN_APP_KEY || '',
  region: 'cn-shanghai',
  endpoint: 'http://nls-meta.cn-shanghai.aliyuncs.com',
};

export interface AliyunASRResult {
  success: boolean;
  transcript?: string;
  duration?: number; // 音频时长（毫秒）
  cost?: number; // 费用估算（元）
  error?: string;
}

/**
 * 检查阿里云配置是否完整
 */
export function checkAliyunConfig(): { valid: boolean; missing: string[] } {
  const missing: string[] = [];
  
  if (!ALIYUN_CONFIG.accessKeyId) missing.push('ALIYUN_ACCESS_KEY_ID');
  if (!ALIYUN_CONFIG.accessKeySecret) missing.push('ALIYUN_ACCESS_KEY_SECRET');
  if (!ALIYUN_CONFIG.appKey) missing.push('ALIYUN_APP_KEY');
  
  return { valid: missing.length === 0, missing };
}

/**
 * 提交音频转写任务
 * 
 * 流程:
 * 1. 获取 Token
 * 2. 提交转写任务（视频URL）
  * 3. 轮询查询结果
 * 4. 返回转写文本
 * 
 * @param audioUrl - 音频/视频 URL
 * @returns AliyunASRResult
 */
export async function transcribeAudio(audioUrl: string): Promise<AliyunASRResult> {
  // 检查配置
  const configCheck = checkAliyunConfig();
  if (!configCheck.valid) {
    return {
      success: false,
      error: `阿里云配置不完整，缺少: ${configCheck.missing.join(', ')}`
    };
  }
  
  try {
    console.log(`[AliyunASR] 开始转写: ${audioUrl.substring(0, 80)}...`);
    
    // 步骤1: 获取 Token
    const token = await getAliyunToken();
    if (!token) {
      return { success: false, error: '获取阿里云 Token 失败' };
    }
    
    // 步骤2: 提交转写任务
    const taskId = await submitTask(audioUrl, token);
    if (!taskId) {
      return { success: false, error: '提交转写任务失败' };
    }
    
    console.log(`[AliyunASR] 任务已提交: ${taskId}`);
    
    // 步骤3: 轮询查询结果（最多60秒）
    const result = await pollTaskResult(taskId, token);
    
    return result;
    
  } catch (error) {
    console.error('[AliyunASR] Error:', error);
    return {
      success: false,
      error: `转写失败: ${error instanceof Error ? error.message : '未知错误'}`
    };
  }
}

/**
 * 获取阿里云 Token
 */
async function getAliyunToken(): Promise<string | null> {
  try {
    // 构造签名
    const date = new Date().toUTCString();
    const signature = generateSignature(date);
    
    const response = await fetch('https://nls-meta.cn-shanghai.aliyuncs.com/pop/2019-02-28/tokens', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Date': date,
        'Authorization': `acs ${ALIYUN_CONFIG.accessKeyId}:${signature}`,
      },
      body: JSON.stringify({
        appKey: ALIYUN_CONFIG.appKey,
      }),
    });
    
    if (!response.ok) {
      const error = await response.text();
      console.error('[AliyunASR] Token request failed:', error);
      return null;
    }
    
    const data = await response.json() as any;
    return data?.Token?.Id || null;
    
  } catch (error) {
    console.error('[AliyunASR] Get token error:', error);
    return null;
  }
}

/**
 * 生成阿里云签名
 */
function generateSignature(date: string): string {
  // 简化版签名，实际需要按阿里云规范实现
  // 参考: https://help.aliyun.com/document_detail/90780.html
  const stringToSign = `POST\napplication/json\n${date}\nx-acs-signature-method:HMAC-SHA1\nx-acs-signature-version:1.0\n/pop/2019-02-28/tokens`;
  
  // 使用 HMAC-SHA1 签名
  const crypto = require('crypto');
  const hmac = crypto.createHmac('sha1', ALIYUN_CONFIG.accessKeySecret);
  hmac.update(stringToSign);
  return hmac.digest('base64');
}

/**
 * 提交转写任务
 */
async function submitTask(audioUrl: string, token: string): Promise<string | null> {
  try {
    const response = await fetch('https://filetrans.cn-shanghai.aliyuncs.com/pop/2022-12-14/filetrans/submitTask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-NLS-Token': token,
      },
      body: JSON.stringify({
        appkey: ALIYUN_CONFIG.appKey,
        fileLink: audioUrl,
        // 配置参数
        config: {
          outputFormat: 'txt', // 输出纯文本
          enablePunctuation: true, // 启用标点
          enableInverseTextNormalization: true, // 数字转换
        },
      }),
    });
    
    if (!response.ok) {
      const error = await response.text();
      console.error('[AliyunASR] Submit task failed:', error);
      return null;
    }
    
    const data = await response.json() as any;
    
    if (data?.StatusCode !== 21050000) {
      console.error('[AliyunASR] Submit task error:', data);
      return null;
    }
    
    return data?.TaskId || null;
    
  } catch (error) {
    console.error('[AliyunASR] Submit task error:', error);
    return null;
  }
}

/**
 * 轮询查询任务结果
 */
async function pollTaskResult(taskId: string, token: string, maxWaitMs: number = 60000): Promise<AliyunASRResult> {
  const startTime = Date.now();
  const pollInterval = 2000; // 2秒轮询一次
  
  while (Date.now() - startTime < maxWaitMs) {
    try {
      const response = await fetch(`https://filetrans.cn-shanghai.aliyuncs.com/pop/2022-12-14/filetrans/getTaskResult?appkey=${ALIYUN_CONFIG.appKey}&taskId=${taskId}`, {
        method: 'GET',
        headers: {
          'X-NLS-Token': token,
        },
      });
      
      if (!response.ok) {
        await new Promise(r => setTimeout(r, pollInterval));
        continue;
      }
      
      const data = await response.json() as any;
      
      // 状态码说明:
      // 21050000: 成功
      // 21050001: 处理中
      // 其他: 错误
      
      if (data?.StatusCode === 21050000) {
        // 任务完成
        const resultText = extractResultText(data);
        const duration = data?.Result?.AudioDuration || 0;
        
        return {
          success: true,
          transcript: resultText,
          duration: duration,
          cost: estimateCost(duration),
        };
      } else if (data?.StatusCode === 21050001) {
        // 仍在处理中，继续轮询
        console.log(`[AliyunASR] 处理中... (${Math.round((Date.now() - startTime) / 1000)}s)`);
      } else {
        // 处理失败
        return {
          success: false,
          error: `转写失败: ${data?.StatusText || '未知错误'}`
        };
      }
      
    } catch (error) {
      console.error('[AliyunASR] Poll error:', error);
    }
    
    await new Promise(r => setTimeout(r, pollInterval));
  }
  
  return {
    success: false,
    error: '转写超时'
  };
}

/**
 * 从结果中提取文本
 */
function extractResultText(data: any): string {
  try {
    const sentences = data?.Result?.Sentences || [];
    return sentences.map((s: any) => s.Text).join('');
  } catch {
    return '';
  }
}

/**
 * 估算费用
 * 阿里云价格: ¥2.5/小时，最低按15秒计费
 */
function estimateCost(durationMs: number): number {
  const minutes = durationMs / 1000 / 60;
  const hours = minutes / 60;
  return Math.max(0.01, hours * 2.5); // 最低¥0.01
}
