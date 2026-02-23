import { Router } from 'express';
import { DeepSeekClient } from '@auto-home/ai';

const router = Router();

// 初始化 DeepSeek 客户端
const aiClient = new DeepSeekClient(
  process.env.DEEPSEEK_API_KEY || '',
  process.env.DEEPSEEK_BASE_URL
);

// POST /api/ai/rewrite
router.post('/rewrite', async (req, res) => {
  try {
    const { text } = req.body;

    if (!text || typeof text !== 'string') {
      res.status(400).json({ error: 'Missing text parameter' });
      return;
    }

    if (!process.env.DEEPSEEK_API_KEY) {
      res.status(500).json({ error: 'AI service not configured' });
      return;
    }

    const result = await aiClient.rewritePropertyScript(text);
    res.json(result);
  } catch (error) {
    console.error('Rewrite error:', error);
    res.status(500).json({ error: 'Failed to rewrite text' });
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
