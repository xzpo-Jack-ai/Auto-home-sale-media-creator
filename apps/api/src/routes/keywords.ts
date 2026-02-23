import { Router } from 'express';

const router = Router();

// 模拟热词数据
const mockKeywords: Record<string, string[]> = {
  '北京': ['北京二手房降价潮', '海淀学区房最新政策', '朝阳改善型房源'],
  '上海': ['上海房贷新政解读', '浦东内环新房开盘', '老破小还值得买吗'],
  '深圳': ['深圳楼市触底反弹', '南山科技园周边租房', '福田豪宅降价百万'],
  '广州': ['广州买房攻略2024', '天河区学位房', '增城刚需盘推荐'],
  '杭州': ['杭州亚运会后房价', '未来科技城裁员潮', '西湖区老洋房'],
  '成都': ['成都天府新区规划', '高新区人才公寓', '锦江区学区房'],
};

// GET /api/keywords?city=北京
router.get('/', (req, res) => {
  const city = (req.query.city as string) || '北京';
  const keywords = mockKeywords[city] || ['房产市场分析', '买房避坑指南', '房贷利率最新'];
  
  res.json({
    city,
    keywords: keywords.map((k, i) => ({
      id: `${city}-${i}`,
      text: k,
      heat: Math.floor(Math.random() * 50) + 50, // 50-100
    })),
    updatedAt: new Date().toISOString(),
  });
});

// 获取支持的城市列表
router.get('/cities', (req, res) => {
  res.json({
    cities: Object.keys(mockKeywords),
  });
});

export { router as keywordRoutes };
