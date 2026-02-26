#!/usr/bin/env node
/**
 * 调试抖音页面结构
 */

import https from 'https';
import http from 'http';

async function fetchHtml(url: string): Promise<string | null> {
  return new Promise((resolve) => {
    const client = url.startsWith('https') ? https : http;
    
    const options = {
      hostname: new URL(url).hostname,
      path: new URL(url).pathname + new URL(url).search,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.douyin.com/',
      },
      timeout: 15000,
    };

    const req = client.request(options, (res) => {
      let data = '';
      res.setEncoding('utf8');
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    });

    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
    req.end();
  });
}

async function resolveShortUrl(shortUrl: string): Promise<string | null> {
  return new Promise((resolve) => {
    const url = new URL(shortUrl);
    const client = url.protocol === 'https:' ? https : http;
    
    const options = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'HEAD',
      headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': '*/*',
      },
      timeout: 10000,
    };

    const req = client.request(options, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        const location = res.headers.location;
        if (location) {
          const match = location.match(/\/video\/(\d+)/);
          if (match) { resolve(match[1]); return; }
        }
      }
      const match = shortUrl.match(/\/video\/(\d+)/);
      resolve(match ? match[1] : null);
    });

    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
    req.end();
  });
}

async function main() {
  const url = process.argv[2] || 'https://v.douyin.com/od9jc8Ju4t8/';
  
  console.log('🔍 调试抖音页面结构\n');
  
  // 1. 解析短链接
  const videoId = await resolveShortUrl(url);
  console.log(`Video ID: ${videoId}`);
  
  // 2. 获取页面
  const webUrl = `https://www.douyin.com/video/${videoId}`;
  console.log(`Fetching: ${webUrl}\n`);
  
  const html = await fetchHtml(webUrl);
  if (!html) {
    console.log('❌ 无法获取页面');
    return;
  }
  
  console.log(`HTML长度: ${html.length}\n`);
  
  // 3. 查找数据结构
  console.log('--- 查找 RENDER_DATA ---');
  const renderMatch = html.match(/<script[^>]*id="RENDER_DATA"[^>]*>(.+?)<\/script>/s);
  if (renderMatch) {
    console.log('✅ 找到 RENDER_DATA');
    console.log(`内容长度: ${renderMatch[1].length}`);
    console.log(`前500字符:\n${renderMatch[1].substring(0, 500)}\n`);
  } else {
    console.log('❌ 未找到 RENDER_DATA\n');
  }
  
  console.log('--- 查找 SSR_HYDRATED_DATA ---');
  const ssrMatch = html.match(/window\._SSR_HYDRATED_DATA\s*=\s*(\{.+?\});/s);
  if (ssrMatch) {
    console.log('✅ 找到 SSR_HYDRATED_DATA');
    console.log(`内容长度: ${ssrMatch[1].length}\n`);
  } else {
    console.log('❌ 未找到 SSR_HYDRATED_DATA\n');
  }
  
  console.log('--- 查找 __INITIAL_STATE__ ---');
  const initMatch = html.match(/window\.__INITIAL_STATE__\s*=\s*(\{.+?\});/s);
  if (initMatch) {
    console.log('✅ 找到 __INITIAL_STATE__');
    console.log(`内容长度: ${initMatch[1].length}\n`);
  } else {
    console.log('❌ 未找到 __INITIAL_STATE__\n');
  }
  
  // 4. 保存HTML用于分析
  const fs = await import('fs');
  const path = `/tmp/douyin_debug_${videoId}.html`;
  fs.writeFileSync(path, html);
  console.log(`HTML已保存: ${path}`);
  
  // 5. 查找任何包含字幕相关的内容
  console.log('\n--- 查找字幕相关关键词 ---');
  const keywords = ['subtitle', 'caption', '字幕', 'utterances'];
  for (const kw of keywords) {
    const idx = html.toLowerCase().indexOf(kw);
    if (idx !== -1) {
      console.log(`✅ 找到 "${kw}" @ position ${idx}`);
      console.log(`   上下文: ${html.substring(Math.max(0, idx-50), idx+100)}\n`);
    }
  }
}

main().catch(console.error);
