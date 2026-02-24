/**
 * 手动录入真实视频数据
 * 用于测试 AI 洗稿功能
 */

import { prisma } from './prisma';

const REAL_VIDEOS = [
  {
    // 用户提供：杭州跌价公寓
    externalId: 'douyin-AWw1YCIy6ek',
    platform: 'douyin' as const,
    title: '杭州跌的最惨的小区100变26，当天可以拎包入住，冰箱洗衣机沙发柜子床全送',
    author: '杭州房产博主',
    authorId: 'hz_user_001',
    views: 2350000,  // 估算：2.35
    likes: 45000,
    shares: 3200,
    comments: 2800,
    coverUrl: 'https://picsum.photos/300/400?random=hz001',
    duration: 45,
    transcript: `杭州跌的最惨的小区，100万变成26万！
这套房子当天就可以拎包入住，冰箱、洗衣机、沙发、柜子、床全送！
房东急售，价格还可以谈。
位于杭州西湖区，周边配套成熟，交通便利。
对于刚需上车的朋友来说，这是一个难得的捡漏机会。
感兴趣的赶紧私信我，好房不等人！`,
    publishedAt: new Date('2024-02-20'),
    keyword: '杭州跌价房',
    city: '杭州',
    tags: ['捡漏', '公寓', '抖音房产', '杭州西湖区', '杭州买房'],
  },
];

async function seedRealVideos() {
  console.log('📝 Seeding real video data...');

  for (const video of REAL_VIDEOS) {
    // 插入或更新视频
    const created = await prisma.video.upsert({
      where: { externalId: video.externalId },
      update: {
        title: video.title,
        transcript: video.transcript,
        views: video.views,
        likes: video.likes,
      },
      create: {
        externalId: video.externalId,
        platform: video.platform,
        title: video.title,
        author: video.author,
        authorId: video.authorId,
        views: video.views,
        likes: video.likes,
        shares: video.shares,
        comments: video.comments,
        coverUrl: video.coverUrl,
        duration: video.duration,
        transcript: video.transcript,
        publishedAt: video.publishedAt,
        keyword: video.keyword,
        city: video.city,
      },
    });

    console.log(`✅ Video saved: ${created.title.substring(0, 30)}...`);

    // 确保关键词存在
    await prisma.keyword.upsert({
      where: {
        city_text: {
          city: video.city,
          text: video.keyword,
        },
      },
      update: { heat: 95 },
      create: {
        city: video.city,
        text: video.keyword,
        heat: 95,
      },
    });

    console.log(`✅ Keyword ensured: ${video.city} - ${video.keyword}`);
  }

  console.log('🎉 Real video data seeded successfully!');
}

seedRealVideos()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
