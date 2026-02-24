import { Router } from 'express';
import { KeywordDAO } from '../services/keyword.service';

const router = Router();

// GET /api/keywords?city=北京
router.get('/', async (req, res) => {
  try {
    const city = (req.query.city as string) || '北京';
    const keywords = await KeywordDAO.getByCity(city);

    res.json({
      city,
      keywords,
      updatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Failed to fetch keywords:', error);
    res.status(500).json({ error: 'Failed to fetch keywords' });
  }
});

// 获取支持的城市列表
router.get('/cities', async (req, res) => {
  try {
    const cities = await KeywordDAO.getCities();
    res.json({ cities });
  } catch (error) {
    console.error('Failed to fetch cities:', error);
    res.status(500).json({ error: 'Failed to fetch cities' });
  }
});

export { router as keywordRoutes };
