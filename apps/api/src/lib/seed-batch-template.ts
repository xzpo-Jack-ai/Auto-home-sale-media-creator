/**
 * 批量录入模板 - 快速验证阶段
 * 使用方法：
 * 1. 复制此文件为 seed-batch.ts
 * 2. 填写 videoData 数组
 * 3. 运行: npx tsx seed-batch.ts
 */

import { prisma } from './prisma';

// 在这里添加视频数据
const videoData = [
  // 示例格式：
  {
    link: 'https://v.douyin.com/xxxxx/',
    city: '杭州',
    keyword: '杭州学区房',
    title: '视频标题（从文案提取）',
    author: '作者名',
    transcript: '完整的视频口播文案...',
    views: 1000000,  // 播放量（从链接前的数字估算）
    likes: 20000,    // 点赞数（从链接前的估算）
  },
  // 继续添加更多...
];

async function batchInsert() {
  console.log(`📝 准备录入 ${videoData.length} 个视频...`);

  for (const data of videoData) {
    try {
      // 解析链接
      const shortCode = data.link.match(/v\.douyin\.com\/([a-zA-Z0-9]+)/)?.[1] || Date.now();
      
      // 创建视频
      const video = await prisma.video.create({
        data: {
          externalId: `douyin-${shortCode}`,
          platform: 'douyin',
          title: data.title,
          author: data.author,
          views: data.views,
          likes: data.likes,
          transcript: data.transcript,
          coverUrl: `https://picsum.photos/300/400?random=${shortCode}`,
          publishedAt: new Date(),
          keyword: data.keyword,
          city: data.city,
        },
      });

      // 更新关键词热度
      await prisma.keyword.upsert({
        where: {
          city_text: { city: data.city, text: data.keyword },
        },
        update: {
          heat: Math.min(95 + (data.views / 1000000), 100),
        },
        create: {
          city: data.city,
          text: data.keyword,
          heat: Math.min(95 + (data.views / 1000000), 100),
        },
      });

      console.log(`✅ 已录入: ${data.title.substring(0, 30)}...`);
    } catch (error) {
      console.error(`❌ 录入失败: ${data.title}`, error);
    }
  }

  console.log('🎉 批量录入完成！');
}

// 统计信息
async function showStats() {
  const stats = await prisma.video.groupBy({
    by: ['city', 'keyword'],
    _count: { id: true },
  });
  
  console.log('\n📊 当前数据分布:');
  for (const s of stats) {
    console.log(`  ${s.city} - ${s.keyword}: ${s._count.id} 个视频`);
  }
}

// 如果直接运行
if (require.main === module) {
  batchInsert()
    .then(() => showStats())
    .catch(console.error)
    .finally(() => prisma.$disconnect());
}

export { videoData, batchInsert };
