#!/usr/bin/env node
/**
 * 字幕提取 CLI 测试工具
 * 
 * 用法：
 *   npx tsx scripts/test-subtitle.ts <抖音链接>
 *   npx tsx scripts/test-subtitle.ts https://v.douyin.com/xxxxx
 * 
 * @author ShadowJack
 * @date 2026-02-25
 */

import { extractDouyinSubtitle } from '../src/services/subtitle-extractor';

async function main() {
  const url = process.argv[2];
  
  if (!url) {
    console.error('❌ 请提供抖音链接');
    console.error('用法: npx tsx scripts/test-subtitle.ts <抖音链接>');
    console.error('示例: npx tsx scripts/test-subtitle.ts https://v.douyin.com/i5QF7WfJ/');
    process.exit(1);
  }

  console.log('🚀 开始提取字幕...');
  console.log(`🔗 URL: ${url}\n`);

  const startTime = Date.now();
  
  try {
    const result = await extractDouyinSubtitle(url);
    const duration = Date.now() - startTime;
    
    console.log(`\n✅ 提取完成 (${duration}ms)\n`);
    console.log('=====================================');
    
    if (result.success) {
      console.log('📝 标题:', result.title || 'N/A');
      console.log('👤 作者:', result.author || 'N/A');
      console.log('⏱️  时长:', result.duration ? `${result.duration}秒` : 'N/A');
      console.log('📊 来源:', result.source);
      console.log('📝 字数:', result.transcript?.length || 0);
      console.log('\n--- 文案内容 ---');
      console.log(result.transcript);
    } else {
      console.log('❌ 提取失败');
      console.log('错误:', result.error);
    }
    
    console.log('=====================================\n');
    
  } catch (error) {
    console.error('💥 执行失败:', error);
    process.exit(1);
  }
}

main();
