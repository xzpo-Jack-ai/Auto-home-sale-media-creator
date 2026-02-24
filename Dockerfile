# 房产自媒体助手 - 生产环境 Dockerfile

# 阶段1：构建前端
FROM node:20-alpine AS web-builder
WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm@9.15.0

# 复制依赖文件
COPY package.json pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json ./apps/web/
COPY packages/*/package.json ./packages/*/

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建前端
RUN pnpm --filter web build

# 阶段2：构建后端
FROM node:20-alpine AS api-builder
WORKDIR /app

RUN npm install -g pnpm@9.15.0

COPY package.json pnpm-workspace.yaml turbo.json ./
COPY apps/api/package.json ./apps/api/
COPY packages/*/package.json ./packages/*/

RUN pnpm install --frozen-lockfile

COPY . .

# 生成 Prisma 客户端并构建
RUN cd apps/api && npx prisma generate && pnpm build

# 阶段3：生产环境
FROM node:20-alpine AS production
WORKDIR /app

RUN npm install -g pnpm@9.15.0

# 安装生产依赖
COPY package.json pnpm-workspace.yaml ./
COPY apps/api/package.json ./apps/api/
COPY packages/*/package.json ./packages/*/

RUN pnpm install --prod --frozen-lockfile

# 复制构建产物
COPY --from=api-builder /app/apps/api/dist ./apps/api/dist
COPY --from=api-builder /app/apps/api/prisma ./apps/api/prisma
COPY --from=web-builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=web-builder /app/apps/web/public ./apps/web/public

# 设置环境变量
ENV NODE_ENV=production
ENV PORT=3001

EXPOSE 3001

# 启动命令
CMD ["node", "apps/api/dist/index.js"]
