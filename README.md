# Auto Home Sale Media Creator

为房产经纪人打造的自媒体内容创作工具

## 功能特性

- 🔥 **热词追踪** - 城市级房产热词自动更新
- 🎬 **爆款分析** - Top20 热门视频参考
- 🤖 **AI 洗稿** - DeepSeek V3 智能改写文案
- 📱 **一键发布** - 快捷发布到抖音/视频号

## 技术栈

- **前端**: Next.js 14 + TailwindCSS + TypeScript
- **后端**: Node.js + Express + Prisma
- **AI**: DeepSeek V3
- **数据库**: PostgreSQL + Redis

## 快速开始

```bash
# 安装依赖
pnpm install

# 启动数据库
docker-compose -f infra/docker-compose.yml up -d

# 配置环境变量
cp .env.example .env
# 编辑 .env 添加 DeepSeek API Key

# 启动开发服务器
pnpm dev
```

访问 http://localhost:3000

## 项目结构

```
auto-home-sale-media-creator/
├── apps/
│   ├── web/          # Next.js 前端
│   └── api/          # Express 后端
├── packages/
│   ├── shared/       # 共享类型
│   └── ai/           # DeepSeek 封装
└── infra/            # Docker 配置
```

## License

MIT
