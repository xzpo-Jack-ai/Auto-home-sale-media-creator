/**
 * DeepSeek LLM 客户端封装
 * 用于文案改写和拍摄指导生成
 */

import OpenAI from 'openai';

export interface RewriteResult {
  versions: string[];
  shootingTips: string[];
  suggestedTags: string[];
}

export class DeepSeekClient {
  private client: OpenAI;
  private model: string;

  constructor(apiKey: string, baseURL: string = 'https://api.deepseek.com/v1') {
    this.client = new OpenAI({
      apiKey,
      baseURL,
    });
    this.model = 'deepseek-chat'; // DeepSeek-V3
  }

  /**
   * 改写房产视频文案
   * @param originalText 原始文案
   * @returns 改写结果
   */
  async rewritePropertyScript(originalText: string): Promise<RewriteResult> {
    const prompt = `你是一位专业的房产自媒体内容顾问。

请将以下房产视频文案改写为3个不同风格的版本，并提供拍摄建议。

原始文案：
"""
${originalText}
"""

请按以下JSON格式输出：
{
  "versions": [
    "版本1：专业权威风格",
    "版本2：亲和易懂风格", 
    "版本3：悬念吸引风格"
  ],
  "shootingTips": [
    "拍摄建议1：场景/镜头建议",
    "拍摄建议2：语速/情绪建议",
    "拍摄建议3：BGM/字幕建议"
  ],
  "suggestedTags": ["标签1", "标签2", "标签3", "标签4", "标签5"]
}

要求：
- 保留核心房源信息（价格、位置、户型等关键数字）
- 每个版本100-200字
- 拍摄建议要具体可操作
- 标签要贴合房产自媒体热门标签`;

    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: [
          {
            role: 'system',
            content: '你是一个专业的房产自媒体内容创作助手，擅长改写文案和提供拍摄建议。输出必须是合法的JSON格式。',
          },
          { role: 'user', content: prompt },
        ],
        temperature: 0.7,
        response_format: { type: 'json_object' },
      });

      const content = response.choices[0]?.message?.content;
      if (!content) {
        throw new Error('Empty response from DeepSeek');
      }

      const result = JSON.parse(content) as RewriteResult;
      return {
        versions: result.versions || [],
        shootingTips: result.shootingTips || [],
        suggestedTags: result.suggestedTags || [],
      };
    } catch (error) {
      console.error('DeepSeek rewrite error:', error);
      throw new Error('文案改写失败，请稍后重试');
    }
  }

  /**
   * 生成发布标签
   * @param content 视频内容描述
   * @returns 推荐标签
   */
  async generateTags(content: string): Promise<string[]> {
    const prompt = `为以下房产视频内容生成5-8个合适的抖音/视频号标签：

内容：${content}

请直接输出标签数组，格式：["标签1", "标签2", ...]`;

    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.5,
      });

      const content = response.choices[0]?.message?.content || '[]';
      // 尝试解析JSON数组
      try {
        return JSON.parse(content);
      } catch {
        // 如果解析失败，按行分割提取标签
        return content
          .split(/[\n,，]/)
          .map((t) => t.replace(/[#\[\]"']/g, '').trim())
          .filter((t) => t.length > 0);
      }
    } catch (error) {
      console.error('Tag generation error:', error);
      return ['房产', '买房攻略', '楼市', '好房推荐'];
    }
  }
}

export { OpenAI };
