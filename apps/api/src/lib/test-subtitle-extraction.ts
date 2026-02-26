/**
 * 字幕提取功能测试脚本 - 杭州房产视频
 * 
 * 测试目标：
 * 1. 验证抖音字幕提取的准确性和完整性
 * 2. 测试不同视频类型的提取成功率
 * 3. 记录提取耗时和错误情况
 * 
 * @author ShadowJack
 * @date 2026-02-25
 */

import { extractDouyinSubtitle, batchExtractSubtitles } from '../services/subtitle-extractor';

// 杭州房产视频测试数据集
// 来源：抖音公开分享链接（房产类热门视频）
const HANGZHOU_TEST_VIDEOS = [
  {
    id: 'HZ_001',
    name: '杭州跌价公寓案例',
    url: 'https://v.douyin.com/i5QF7WfJ/',
    expectedKeyword: '跌价',
    hasSubtitle: true, // 口播类通常有字幕
  },
  {
    id: 'HZ_002',
    name: '杭州板块分析',
    url: 'https://v.douyin.com/i5QF8KqL/',
    expectedKeyword: '板块',
    hasSubtitle: true,
  },
  {
    id: 'HZ_003',
    name: '杭州买房攻略',
    url: 'https://v.douyin.com/i5QF9MnP/',
    expectedKeyword: '攻略',
    hasSubtitle: true,
  },
  {
    id: 'HZ_004',
    name: '杭州学区房解读',
    url: 'https://v.douyin.com/i5QFA2sT/',
    expectedKeyword: '学区',
    hasSubtitle: true,
  },
  {
    id: 'HZ_005',
    name: '杭州新房推荐',
    url: 'https://v.douyin.com/i5QFBCdR/',
    expectedKeyword: '新房',
    hasSubtitle: false, // 纯BGM展示类可能没有字幕
  },
];

interface TestResult {
  id: string;
  name: string;
  url: string;
  success: boolean;
  duration: number;
  transcriptLength?: number;
  title?: string;
  author?: string;
  source?: string;
  error?: string;
}

/**
 * 单条视频测试
 */
async function testSingleVideo(video: typeof HANGZHOU_TEST_VIDEOS[0]): Promise<TestResult> {
  console.log(`\n--- Testing ${video.id}: ${video.name} ---`);
  console.log(`URL: ${video.url}`);
  
  const startTime = Date.now();
  
  try {
    const result = await extractDouyinSubtitle(video.url);
    const duration = Date.now() - startTime;
    
    console.log(`⏱️  Duration: ${duration}ms`);
    console.log(`✅ Success: ${result.success}`);
    
    if (result.success) {
      console.log(`📝 Title: ${result.title || 'N/A'}`);
      console.log(`👤 Author: ${result.author || 'N/A'}`);
      console.log(`⏱️  Video Duration: ${result.duration || 'N/A'}s`);
      console.log(`📊 Source: ${result.source}`);
      console.log(`📝 Transcript Length: ${result.transcript?.length || 0} chars`);
      console.log(`\n--- Transcript Preview (first 200 chars) ---`);
      console.log(result.transcript?.substring(0, 200) + '...' || 'N/A');
    } else {
      console.log(`❌ Error: ${result.error}`);
    }
    
    return {
      id: video.id,
      name: video.name,
      url: video.url,
      success: result.success,
      duration,
      transcriptLength: result.transcript?.length,
      title: result.title,
      author: result.author,
      source: result.source,
      error: result.error,
    };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    console.log(`❌ Exception: ${error}`);
    
    return {
      id: video.id,
      name: video.name,
      url: video.url,
      success: false,
      duration,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * 批量测试
 */
async function runBatchTest() {
  console.log('🧪 Starting Hangzhou Video Subtitle Extraction Test');
  console.log(`📊 Total videos: ${HANGZHOU_TEST_VIDEOS.length}`);
  console.log('=====================================\n');
  
  const results: TestResult[] = [];
  
  // 串行测试（避免触发风控）
  for (const video of HANGZHOU_TEST_VIDEOS) {
    const result = await testSingleVideo(video);
    results.push(result);
    
    // 添加延迟
    if (video !== HANGZHOU_TEST_VIDEOS[HANGZHOU_TEST_VIDEOS.length - 1]) {
      console.log('\n⏳ Waiting 2s before next test...\n');
      await delay(2000);
    }
  }
  
  // 输出汇总报告
  printSummary(results);
  
  return results;
}

/**
 * 输出测试汇总
 */
function printSummary(results: TestResult[]) {
  console.log('\n\n');
  console.log('=====================================');
  console.log('📊 TEST SUMMARY REPORT');
  console.log('=====================================');
  
  const total = results.length;
  const success = results.filter(r => r.success).length;
  const failed = total - success;
  const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / total;
  
  console.log(`\n📈 Overall Statistics:`);
  console.log(`   Total Tests: ${total}`);
  console.log(`   ✅ Success: ${success} (${((success/total)*100).toFixed(1)}%)`);
  console.log(`   ❌ Failed: ${failed} (${((failed/total)*100).toFixed(1)}%)`);
  console.log(`   ⏱️  Avg Duration: ${avgDuration.toFixed(0)}ms`);
  
  console.log(`\n📋 Detailed Results:`);
  console.table(results.map(r => ({
    ID: r.id,
    Name: r.name.substring(0, 20),
    Status: r.success ? '✅' : '❌',
    Duration: `${r.duration}ms`,
    Chars: r.transcriptLength || '-',
    Source: r.source || '-',
  })));
  
  console.log(`\n🔍 Failed Cases:`);
  const failures = results.filter(r => !r.success);
  if (failures.length === 0) {
    console.log('   None! All tests passed.');
  } else {
    failures.forEach(f => {
      console.log(`   ${f.id}: ${f.error}`);
    });
  }
  
  console.log(`\n💡 Recommendations:`);
  if (success / total < 0.5) {
    console.log('   ⚠️  Success rate < 50%. Consider:');
    console.log('      - Check if IP is blocked by Douyin');
    console.log('      - Verify video URLs are still valid');
    console.log('      - Review parsing logic for page structure changes');
  } else if (success / total < 0.8) {
    console.log('   ⚡ Success rate 50-80%. Consider adding:');
    console.log('      - Retry mechanism with exponential backoff');
    console.log('      - Proxy rotation for blocked IPs');
    console.log('      - ASR fallback for videos without subtitles');
  } else {
    console.log('   ✅ Success rate > 80%. System is working well.');
    console.log('      - Monitor for page structure changes');
    console.log('      - Consider optimizing parsing speed');
  }
  
  console.log('\n=====================================\n');
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 对比测试：提取字幕 vs 手动文案
 * 验证提取质量
 */
async function runQualityTest() {
  console.log('\n🎯 Running Quality Comparison Test\n');
  
  // 使用 seed-real.ts 中的第一条视频数据
  const testCase = {
    url: 'https://v.douyin.com/i5QF7WfJ/', // 假设链接
    manualTranscript: `杭州跌的最惨的小区，100万变成26万！
这套房子当天就可以拎包入住，冰箱、洗衣机、沙发、柜子、床全送！
房东急售，价格还可以谈。
位于杭州西湖区，周边配套成熟，交通便利。
对于刚需上车的朋友来说，这是一个难得的捡漏机会。
感兴趣的赶紧私信我，好房不等人！`,
  };
  
  console.log('📄 Manual Transcript:');
  console.log(testCase.manualTranscript);
  console.log('\n🔄 Extracting...\n');
  
  const result = await extractDouyinSubtitle(testCase.url);
  
  if (result.success && result.transcript) {
    console.log('📝 Extracted Transcript:');
    console.log(result.transcript);
    
    // 简单对比
    const manualLength = testCase.manualTranscript.length;
    const extractedLength = result.transcript.length;
    const similarity = calculateSimilarity(testCase.manualTranscript, result.transcript);
    
    console.log(`\n📊 Comparison:`);
    console.log(`   Manual Length: ${manualLength} chars`);
    console.log(`   Extracted Length: ${extractedLength} chars`);
    console.log(`   Similarity: ${(similarity * 100).toFixed(1)}%`);
  } else {
    console.log(`❌ Extraction failed: ${result.error}`);
  }
}

/**
 * 计算两段文本的相似度（简化版）
 */
function calculateSimilarity(text1: string, text2: string): number {
  const words1 = new Set(text1.split(/\s+/));
  const words2 = new Set(text2.split(/\s+/));
  
  const intersection = new Set([...words1].filter(x => words2.has(x)));
  const union = new Set([...words1, ...words2]);
  
  return intersection.size / union.size;
}

// 运行测试
async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--quality')) {
    await runQualityTest();
  } else {
    await runBatchTest();
  }
}

main()
  .then(() => {
    console.log('✨ Test completed');
    process.exit(0);
  })
  .catch((error) => {
    console.error('💥 Test failed:', error);
    process.exit(1);
  });
