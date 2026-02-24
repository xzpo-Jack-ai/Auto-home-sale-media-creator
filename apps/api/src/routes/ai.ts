import { Router } from 'express';
import { DeepSeekClient } from '@auto-home/ai';

const router = Router();

// 初始化 DeepSeek 客户端
const aiClient = new DeepSeekClient(
  process.env.DEEPSEEK_API_KEY || '',
  process.env.DEEPSEEK_BASE_URL
);

// 模拟 AI 改写（当 API 不可用时使用）
function mockRewrite(text: string) {
  return {
    versions: [
      `【专业版】${text.substring(0, 20)}...这套房源位于核心区域，业主急售，价格可谈。周边配套成熟，是投资自住的优质选择。`,
      `【亲和版】家人们！${text.substring(0, 15)}...房东急用钱，价格好商量！家具全送，当天入住，刚需上车的绝佳机会！`,
      `【悬念版】什么样的房子能让买家当场下定？${text.substring(0, 15)}...错过这套，再等一年！`,
    ],
    shootingTips: [
      '开场用广角展示房子全貌，配合"这套房绝了"的口播',
      '中间特写家具赠送细节，语速放慢强调"全送"卖点',
      '结尾加快语速营造紧迫感，引导私信咨询',
    ],
    suggestedTags: ['捡漏', '杭州买房', '公寓', '刚需', '房产'],
  };
}

// POST /api/ai/rewrite
router.post('/rewrite', async (req, res) => {
  try {
    const { text } = req.body;

    if (!text || typeof text !== 'string') {
      res.status(400).json({ error: 'Missing text parameter' });
      return;
    }

    // 如果 API Key 无效，使用模拟数据
    if (!process.env.DEEPSEEK_API_KEY || process.env.DEEPSEEK_API_KEY.includes('invalid')) {
      console.log('Using mock AI response');
      res.json(mockRewrite(text));
      return;
    }

    const result = await aiClient.rewritePropertyScript(text);
    res.json(result);
  } catch (error) {
    console.error('Rewrite error:', error);
    // 降级到模拟数据
    res.json(mockRewrite(req.body.text));
  }
});

// POST /api/ai/generate-tags
router.post('/generate-tags', async (req, res) => {
  try {
    const { content } = req.body;

    if (!content || typeof content !== 'string') {
      res.status(400).json({ error: 'Missing content parameter' });
      return;
    }

    const tags = await aiClient.generateTags(content);
    res.json({ tags });
  } catch (error) {
    console.error('Tag generation error:', error);
    res.status(500).json({ error: 'Failed to generate tags' });
  }
});

export { router as aiRoutes };
