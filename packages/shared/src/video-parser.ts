/**
 * 抖音链接解析器
 * 从分享链接中提取视频信息和文案
 */

export interface ParsedVideoLink {
  platform: 'douyin' | 'video_channel';
  shortCode: string;
  fullUrl: string;
  videoId?: string;
}

/**
 * 解析抖音分享链接
 * 支持格式：
 * - https://v.douyin.com/xxxxx/
 * - https://www.iesdouyin.com/xxxxx
 */
export function parseDouyinLink(link: string): ParsedVideoLink | null {
  // 清理链接（去除中文描述）
  const cleanLink = link.split(' ')[0].trim();
  
  // 匹配抖音短链
  const douyinShortRegex = /https:\/\/v\.douyin\.com\/([a-zA-Z0-9]+)/i;
  const douyinFullRegex = /https:\/\/www\.iesdouyin\.com\/.*\?.*video_id=([0-9]+)/i;
  
  const shortMatch = cleanLink.match(douyinShortRegex);
  if (shortMatch) {
    return {
      platform: 'douyin',
      shortCode: shortMatch[1],
      fullUrl: cleanLink,
    };
  }
  
  const fullMatch = cleanLink.match(douyinFullRegex);
  if (fullMatch) {
    return {
      platform: 'douyin',
      shortCode: '',
      fullUrl: cleanLink,
      videoId: fullMatch[1],
    };
  }
  
  return null;
}

/**
 * 解析视频号链接
 */
export function parseVideoChannelLink(link: string): ParsedVideoLink | null {
  // 视频号链接格式：finder.video.qq.com/xxx
  const channelRegex = /https:\/\/finder\.video\.qq\.com\/([a-zA-Z0-9]+)/i;
  const match = link.match(channelRegex);
  
  if (match) {
    return {
      platform: 'video_channel',
      shortCode: match[1],
      fullUrl: link.split(' ')[0].trim(),
    };
  }
  
  return null;
}

/**
 * 自动识别平台并解析
 */
export function parseVideoLink(link: string): ParsedVideoLink | null {
  return parseDouyinLink(link) || parseVideoChannelLink(link);
}

/**
 * 从分享文本中提取链接
 */
export function extractLinkFromText(text: string): string | null {
  // 匹配 URL
  const urlRegex = /(https?:\/\/[^\s]+)/i;
  const match = text.match(urlRegex);
  return match ? match[1] : null;
}

/**
 * 模拟获取视频详情（实际应调用解析API）
 * 目前先返回模拟数据，后续接入真实解析服务
 */
export async function fetchVideoDetailFromLink(
  link: string
): Promise<{
  title: string;
  transcript: string;
  author: string;
  views: number;
  likes: number;
} | null> {
  const parsed = parseVideoLink(link);
  if (!parsed) {
    return null;
  }
  
  // TODO: 这里应该调用第三方解析API或自建爬虫
  // 目前返回null，表示需要手动录入
  return null;
}
