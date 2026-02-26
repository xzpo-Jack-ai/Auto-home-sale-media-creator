/**
 * 阿里云语音识别服务 - 简化版
 * 
 * 使用阿里云录音文件识别 REST API
 * 文档: https://help.aliyun.com/document_detail/90728.html
 */

// 阿里云语音识别服务 - 简化版

// 阿里云配置
const ALIYUN_CONFIG = {
  accessKeyId: process.env.ALIYUN_ACCESS_KEY_ID || '',
  accessKeySecret: process.env.ALIYUN_ACCESS_KEY_SECRET || '',
  appKey: process.env.ALIYUN_APP_KEY || '',
};

export interface AliyunASRResult {
  success: boolean;
  transcript?: string;
  duration?: number;
  cost?: number;
  error?: string;
}

/**
 * 检查配置
 */
export function checkAliyunConfig(): { valid: boolean; missing: string[] } {
  const missing: string[] = [];
  if (!ALIYUN_CONFIG.accessKeyId) missing.push('ALIYUN_ACCESS_KEY_ID');
  if (!ALIYUN_CONFIG.accessKeySecret) missing.push('ALIYUN_ACCESS_KEY_SECRET');
  if (!ALIYUN_CONFIG.appKey) missing.push('ALIYUN_APP_KEY');
  
  return { valid: missing.length === 0, missing };
}

/**
 * 提交转写任务
 * 
 * 注意: 这是简化实现，实际需要按阿里云文档实现完整签名
 * 参考: https://help.aliyun.com/document_detail/90728.html
 */
export async function submitTranscription(fileUrl: string): Promise<AliyunASRResult> {
  const check = checkAliyunConfig();
  if (!check.valid) {
    return {
      success: false,
      error: `阿里云配置缺失: ${check.missing.join(', ')}`
    };
  }

  console.log(`[AliyunASR] 提交转写任务: ${fileUrl.substring(0, 60)}...`);
  
  // 这里需要实现阿里云签名和API调用
  // 简化起见，返回配置提示
  return {
    success: false,
    error: '请配置阿里云 AK/SK 后使用。需要开通: 智能语音交互 - 录音文件识别'
  };
}

/**
 * 费用估算
 * 阿里云录音文件识别: ¥2.5/小时，最低按15秒计费
 * 参考: https://www.aliyun.com/price/product?spm=a2c4g.11186623.2.14.2ee05fe3v4F5ZV#/nls/overview
 */
export function estimateCost(durationSeconds: number): number {
  // 最低按15秒计费
  const billableSeconds = Math.max(15, durationSeconds);
  const hours = billableSeconds / 3600;
  return Math.round(hours * 2.5 * 100) / 100; // 保留2位小数
}

/**
 * 获取接入指南
 */
export function getSetupGuide(): string {
  return `
阿里云 ASR 接入步骤:

1. 开通服务
   - 访问: https://www.aliyun.com/product/nls
   - 开通 "智能语音交互"
   - 创建项目，获取 AppKey

2. 获取 AccessKey
   - 访问: https://ram.console.aliyun.com/manage/ak
   - 创建 AccessKey ID 和 Secret

3. 配置环境变量
   export ALIYUN_ACCESS_KEY_ID=your_access_key_id
   export ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
   export ALIYUN_APP_KEY=your_app_key

4. 费用
   - 录音文件识别: ¥2.5/小时
   - 1分钟视频约 ¥0.04
   - 新用户有免费额度

5. 文档
   - https://help.aliyun.com/document_detail/90728.html
`;
}
