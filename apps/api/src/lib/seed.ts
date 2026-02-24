import { prisma } from '../lib/prisma';

const CITIES = ['北京', '上海', '深圳', '广州', '杭州', '成都'];

const KEYWORDS: Record<string, string[]> = {
  '北京': ['北京二手房降价潮', '海淀学区房最新政策', '朝阳改善型房源', '通州副中心发展', '顺义别墅区捡漏'],
  '上海': ['上海房贷新政解读', '浦东内环新房开盘', '老破小还值得买吗', '临港自贸区投资', '虹桥商务区租房'],
  '深圳': ['深圳楼市触底反弹', '南山科技园周边租房', '福田豪宅降价百万', '宝安新盘性价比', '龙岗刚需上车'],
  '广州': ['广州买房攻略2024', '天河区学位房', '增城刚需盘推荐', '番禺改善型住宅', '白云区旧改房'],
  '杭州': ['杭州亚运会后房价', '未来科技城裁员潮', '西湖区老洋房', '钱江新城豪宅', '萧山机场周边'],
  '成都': ['成都天府新区规划', '高新区人才公寓', '锦江区学区房', '武侯区改善盘', '成华区地铁房'],
};

const MOCK_VIDEOS = [
  {
    title: '这套房降了200万，业主急售！',
    author: '房产小李',
    authorId: 'user_001',
    views: 1250000,
    likes: 45000,
    shares: 3200,
    comments: 1800,
    duration: 45,
    transcript: '大家好，今天给大家推荐一套超值房源！这套房子位于市中心黄金地段，业主因为换房急售，直降200万！三室两厅两卫，南北通透，采光非常好。小区配套成熟，楼下就是地铁站。喜欢的朋友赶紧私信我！',
  },
  {
    title: '妈妈都在抢的学区房，到底值不值？',
    author: '学区房专家王姐',
    authorId: 'user_002',
    views: 890000,
    likes: 32000,
    shares: 5600,
    comments: 2400,
    duration: 62,
    transcript: '最近很多家长问我学区房到底值不值得买。今天我实地探访了这套热门学区房，给大家分析一下。这套房子对口的是市重点小学，周边配套齐全。但也要提醒大家，学区房政策每年都有变化，购买前一定要做好功课。',
  },
  {
    title: '2024年买房，这三个区域最有潜力',
    author: '房产投资老张',
    authorId: 'user_003',
    views: 2100000,
    likes: 78000,
    shares: 12500,
    comments: 4200,
    duration: 88,
    transcript: '从业15年，我总结了2024年最值得关注的三个区域。第一是新兴科技园区周边，第二是地铁新沿线，第三是老城区改造区。这三个区域未来3年都有较大增值空间，刚需和投资都可以关注。',
  },
  {
    title: '北漂5年，终于凑够首付买了第一套房',
    author: '北漂青年阿杰',
    authorId: 'user_004',
    views: 560000,
    likes: 21000,
    shares: 2800,
    comments: 1500,
    duration: 120,
    transcript: '从月薪5000到买房上车，我用了5年时间。今天分享一下我的买房经历，希望能给同样在北京打拼的年轻人一些参考。选房、看房、谈判、签约，每一步都有坑，我都帮你们踩过了。',
  },
  {
    title: '公园旁边的豪宅，带你看房',
    author: '豪宅顾问Lisa',
    authorId: 'user_005',
    views: 340000,
    likes: 12000,
    shares: 1500,
    comments: 890,
    duration: 95,
    transcript: '今天带看一套公园景观豪宅，200平米大平层，客厅直面公园湖景。这种景观资源在整个城市都是稀缺品。虽然总价较高，但对于追求生活品质的家庭来说，这套房子值得考虑。',
  },
];

export async function seed() {
  console.log('🌱 Seeding database...');

  // 1. 种子热词
  console.log('Seeding keywords...');
  for (const city of CITIES) {
    const keywords = KEYWORDS[city] || [];
    for (const text of keywords) {
      await prisma.keyword.upsert({
        where: {
          city_text: { city, text },
        },
        update: {
          heat: Math.floor(Math.random() * 50) + 50,
        },
        create: {
          city,
          text,
          heat: Math.floor(Math.random() * 50) + 50,
        },
      });
    }
  }

  // 2. 种子视频数据
  console.log('Seeding videos...');
  for (const city of CITIES) {
    for (const keyword of KEYWORDS[city] || []) {
      // 每个关键词下创建5条视频
      for (let i = 0; i < 5; i++) {
        const mockVideo = MOCK_VIDEOS[i % MOCK_VIDEOS.length];
        await prisma.video.upsert({
          where: {
            externalId: `${city}-${keyword}-${i}`,
          },
          update: {},
          create: {
            externalId: `${city}-${keyword}-${i}`,
            platform: Math.random() > 0.5 ? 'douyin' : 'video_channel',
            title: `${city}${keyword} - ${mockVideo.title}`,
            author: mockVideo.author,
            authorId: mockVideo.authorId,
            views: mockVideo.views + Math.floor(Math.random() * 100000),
            likes: mockVideo.likes + Math.floor(Math.random() * 5000),
            shares: mockVideo.shares,
            comments: mockVideo.comments,
            coverUrl: `https://picsum.photos/300/400?random=${city}-${i}`,
            duration: mockVideo.duration,
            transcript: mockVideo.transcript,
            publishedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000), // 30天内
            keyword: keyword,
            city: city,
          },
        });
      }
    }
  }

  console.log('✅ Seeding completed!');
}

// 如果直接运行此文件
if (require.main === module) {
  seed()
    .catch((e) => {
      console.error(e);
      process.exit(1);
    })
    .finally(async () => {
      await prisma.$disconnect();
    });
}
