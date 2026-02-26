import { Router } from 'express';
import { DeepSeekClient } from '@auto-home/ai';

const router = Router();

// 延迟初始化 DeepSeek 客户端（确保 env 已加载）
let aiClient: DeepSeekClient | null = null;
function getAIClient(): DeepSeekClient {
  if (!aiClient) {
    const apiKey = process.env.DEEPSEEK_API_KEY || '';
    console.log('[AI Route] DEEPSEEK_API_KEY:', apiKey ? `已设置 (${apiKey.slice(0, 10)}...)` : '未设置');
    aiClient = new DeepSeekClient(apiKey, process.env.DEEPSEEK_BASE_URL);
  }
  return aiClient;
}

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

    console.log('🤖 Calling DeepSeek API for rewrite...');
    const startTime = Date.now();
    
    const result = await getAIClient().rewritePropertyScript(text);
    
    const duration = Date.now() - startTime;
    console.log(`✅ DeepSeek rewrite completed in ${duration}ms`);
    
    res.json(result);
  } catch (error) {
    console.error('❌ DeepSeek rewrite error:', error);
    res.status(500).json({ 
      error: 'Failed to rewrite text',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
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

    if (!process.env.DEEPSEEK_API_KEY) {
      res.status(500).json({ error: 'AI service not configured' });
      return;
    }

    console.log('🏷️ Calling DeepSeek API for tags...');
    const startTime = Date.now();
    
    const tags = await getAIClient().generateTags(content);
    
    const duration = Date.now() - startTime;
    console.log(`✅ DeepSeek tags generated in ${duration}ms`);
    
    res.json({ tags });
  } catch (error) {
    console.error('❌ Tag generation error:', error);
    res.status(500).json({ 
      error: 'Failed to generate tags',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export { router as aiRoutes };
