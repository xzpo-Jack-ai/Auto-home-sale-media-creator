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
  {
    // 用户提供：杭州板块预警
    externalId: 'douyin-3elAYQ2RtWo',
    platform: 'douyin' as const,
    title: '杭州这四个板块2026年一定格外小心',
    author: '杭州老陈说房',
    authorId: 'hz_user_002',
    views: 7480000,  // 估算：7.48
    likes: 89000,
    shares: 15600,
    comments: 6200,
    coverUrl: 'https://picsum.photos/300/400?random=hz002',
    duration: 72,
    transcript: `杭州这四个板块，2026年一定格外小心！
第一个板块是奥体周边，目前价格已经透支未来3-5年的涨幅空间。
第二个板块是未来科技城，互联网大厂裁员导致购买力下降，房价支撑不足。
第三个板块是勾庄板块，供应量太大，同质化竞争严重。
第四个板块是临安片区，距离主城区太远，配套兑现周期长。
买房不是小事，一定要擦亮眼睛，选对板块比选对房子更重要。
大家有什么想法，评论区聊聊。`,
    publishedAt: new Date('2024-02-21'),
    keyword: '杭州板块预警',
    city: '杭州',
    tags: ['杭州老陈说房', '杭州楼市', '杭州房产', '杭州楼市新政'],
  },
  {
    // 用户提供：杭州买房攻略
    externalId: 'douyin-bUnM6Qq6Utc',
    platform: 'douyin' as const,
    title: '假如26年我给自己在杭州买套房，我会怎么买？',
    author: '杭州老陈说房',
    authorId: 'hz_user_002',
    views: 5640000,  // 估算：5.64
    likes: 72000,
    shares: 11800,
    comments: 4800,
    coverUrl: 'https://picsum.photos/300/400?random=hz003',
    duration: 65,
    transcript: `假如2026年我给自己在杭州买套房，我会怎么买？
第一，我会优先考虑主城区，毕竟配套成熟，抗跌性强。
第二，我会选择地铁沿线，通勤方便，未来转手也容易。
第三，我会关注学区政策，但要注意政策变化风险。
第四，我会控制总价，月供不超过家庭收入的40%，留出生活品质空间。
第五，我会选择品牌开发商，物业质量有保障。
买房是大事，量力而行，不要盲目跟风。
希望这些建议对你有帮助。`,
    publishedAt: new Date('2024-02-15'),
    keyword: '杭州买房攻略',
    city: '杭州',
    tags: ['杭州老陈说房', '杭州楼市', '杭州房产', '杭州楼市新政', '杭州买房新政'],
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
      update: { heat: Math.min(95 + (video.views / 1000000), 100) },
      create: {
        city: video.city,
        text: video.keyword,
        heat: Math.min(95 + (video.views / 1000000), 100),
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
