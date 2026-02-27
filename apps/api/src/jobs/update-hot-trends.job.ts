/**
 * 热词定时更新任务
 * 每天 08:00 自动抓取抖音热榜并更新数据库
 */

import cron from 'node-cron';
import {
  getRealEstateHotTrends,
  saveHotTrendsToDatabase,
} from '../services/douyin-hot.service';

let isRunning = false;

/**
 * 执行热词更新
 */
export async function updateHotTrends(): Promise<void> {
  if (isRunning) {
    console.log('[HotTrendJob] Previous job still running, skipping...');
    return;
  }

  isRunning = true;
  const startTime = Date.now();

  try {
    console.log('[HotTrendJob] Starting hot trends update...');
    console.log(`[HotTrendJob] Time: ${new Date().toISOString()}`);

    // 1. 获取房产热词（按城市分类）
    const cityMap = await getRealEstateHotTrends(50);

    // 2. 统计信息
    let totalItems = 0;
    for (const [city, items] of Object.entries(cityMap)) {
      console.log(`[HotTrendJob] ${city}: ${items.length} items`);
      totalItems += items.length;
    }

    if (totalItems === 0) {
      console.warn('[HotTrendJob] No real estate hot trends found today');
      return;
    }

    // 3. 保存到数据库
    await saveHotTrendsToDatabase(cityMap);

    const duration = Date.now() - startTime;
    console.log(`[HotTrendJob] Completed in ${duration}ms, saved ${totalItems} items`);

  } catch (error) {
    console.error('[HotTrendJob] Failed to update:', error);
    // TODO: 发送告警通知
  } finally {
    isRunning = false;
  }
}

/**
 * 启动定时任务
 * 每天 08:00 执行
 */
export function startHotTrendScheduler(): void {
  console.log('[HotTrendJob] Scheduler initialized');
  console.log('[HotTrendJob] Schedule: Every day at 08:00');

  // 每天 08:00 执行
  cron.schedule('0 8 * * *', async () => {
    console.log('[HotTrendJob] Cron triggered at 08:00');
    await updateHotTrends();
  }, {
    timezone: 'Asia/Shanghai', // 使用中国时区
  });

  console.log('[HotTrendJob] Scheduler started successfully');
}

/**
 * 手动触发（用于测试或首次运行）
 */
export async function manualUpdate(): Promise<void> {
  console.log('[HotTrendJob] Manual update triggered');
  await updateHotTrends();
}

/**
 * 获取下次执行时间
 */
export function getNextRunTime(): Date | null {
  // 简单计算：如果当前 < 08:00，返回今天 08:00；否则返回明天 08:00
  const now = new Date();
  const next = new Date();
  next.setHours(8, 0, 0, 0);

  if (now.getHours() >= 8) {
    next.setDate(next.getDate() + 1);
  }

  return next;
}
