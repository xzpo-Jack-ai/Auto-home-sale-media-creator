#!/usr/bin/env python3
"""
持久化会话 Cookie 管理工具
自动登录并保存 Cookie，支持定期刷新
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright, Page

# 配置
COOKIE_DIR = Path(__file__).parent / "cookies"
COOKIE_DIR.mkdir(exist_ok=True)
COOKIE_FILE = COOKIE_DIR / "douyin_session.json"
SESSION_INFO_FILE = COOKIE_DIR / "session_info.json"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

class PersistentSessionManager:
    """持久化会话管理器"""
    
    def __init__(self):
        self.cookies = None
        self.session_info = self._load_session_info()
    
    def _load_session_info(self):
        """加载会话信息"""
        if SESSION_INFO_FILE.exists():
            with open(SESSION_INFO_FILE, 'r') as f:
                return json.load(f)
        return {
            "created_at": None,
            "last_refresh": None,
            "refresh_count": 0,
            "is_valid": False
        }
    
    def _save_session_info(self):
        """保存会话信息"""
        with open(SESSION_INFO_FILE, 'w') as f:
            json.dump(self.session_info, f, indent=2)
    
    def is_session_valid(self, max_age_hours=24):
        """检查会话是否有效"""
        if not self.session_info["is_valid"]:
            return False
        
        if not self.session_info["last_refresh"]:
            return False
        
        last_refresh = datetime.fromisoformat(self.session_info["last_refresh"])
        age = datetime.now() - last_refresh
        
        return age < timedelta(hours=max_age_hours)
    
    async def interactive_login(self):
        """交互式登录 - 用户扫码后自动保存 Cookie"""
        print("=" * 70)
        print("🔐 抖音持久化会话登录")
        print("=" * 70)
        print("\n即将打开浏览器，请按以下步骤操作：")
        print("1. 在浏览器中使用抖音 App 扫描二维码登录")
        print("2. 登录成功后，按回车键保存 Cookie")
        print("3. Cookie 将自动保存到本地，下次无需重复登录\n")
        print("-" * 70)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--window-size=1400,900']
            )
            
            context = await browser.new_context(
                viewport={'width': 1400, 'height': 900},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            # 访问创作者平台
            print("🌐 正在打开 creator.douyin.com...")
            await page.goto('https://creator.douyin.com', wait_until='networkidle')
            
            # 等待用户登录
            print("⏳ 等待登录...")
            print("   请在浏览器中完成扫码登录")
            print("   登录完成后，请在此按回车键继续...")
            
            input()  # 等待用户按回车
            
            # 验证登录状态
            is_logged_in = await self._verify_login(page)
            
            if not is_logged_in:
                print("\n❌ 未检测到登录状态，请重新运行脚本")
                await browser.close()
                return False
            
            print("\n✅ 登录成功！")
            
            # 获取并保存 Cookie
            cookies = await context.cookies()
            await self._save_cookies(cookies)
            
            # 更新会话信息
            now = datetime.now().isoformat()
            self.session_info.update({
                "created_at": now,
                "last_refresh": now,
                "refresh_count": self.session_info.get("refresh_count", 0) + 1,
                "is_valid": True
            })
            self._save_session_info()
            
            print(f"💾 Cookie 已保存: {COOKIE_FILE}")
            print(f"   共 {len(cookies)} 条 Cookie")
            
            # 显示关键 Cookie
            key_names = ['sessionid', 'sid_tt', 'passport_csrf_token', 'ttwid']
            print("\n🔑 关键 Cookie:")
            for c in cookies:
                if any(key in c['name'] for key in key_names):
                    value_preview = c['value'][:30] + '...' if len(c['value']) > 30 else c['value']
                    print(f"   {c['name']}: {value_preview}")
            
            await browser.close()
            return True
    
    async def _verify_login(self, page: Page) -> bool:
        """验证登录状态"""
        try:
            current_url = page.url
            page_text = await page.evaluate('() => document.body.innerText')
            
            # 检查是否还在登录页
            if 'login' in current_url.lower():
                return False
            
            # 检查是否有登录提示
            login_indicators = ['扫码登录', '验证码登录', '密码登录', '立即登录']
            if any(indicator in page_text for indicator in login_indicators):
                return False
            
            # 检查是否有用户相关元素
            has_user = await page.evaluate('''() => {
                return document.querySelector('[class*="avatar"]') !== null ||
                       document.querySelector('[class*="user-name"]') !== null ||
                       document.body.innerText.includes('创作者中心');
            }''')
            
            return has_user
            
        except Exception as e:
            print(f"验证登录状态时出错: {e}")
            return False
    
    async def _save_cookies(self, cookies):
        """保存 Cookie 到文件"""
        # 只保存 douyin 相关的 cookie
        douyin_cookies = [
            {
                'name': c['name'],
                'value': c['value'],
                'domain': c['domain'],
                'path': c['path'],
                **({'expires': c['expires']} if c.get('expires') else {}),
                **({'secure': c['secure']} if c.get('secure') else {}),
                **({'httpOnly': c['httpOnly']} if c.get('httpOnly') else {}),
            }
            for c in cookies
            if 'douyin' in c.get('domain', '') or 'iesdouyin' in c.get('domain', '')
        ]
        
        with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
            json.dump(douyin_cookies, f, indent=2, ensure_ascii=False)
        
        self.cookies = douyin_cookies
        return douyin_cookies
    
    def load_cookies(self):
        """加载保存的 Cookie"""
        if not COOKIE_FILE.exists():
            return None
        
        with open(COOKIE_FILE, 'r') as f:
            self.cookies = json.load(f)
        
        return self.cookies
    
    async def test_session(self, url=None):
        """测试会话是否有效"""
        url = url or "https://creator.douyin.com/creator-micro/content/manage"
        
        print("=" * 70)
        print("🧪 测试会话有效性")
        print("=" * 70)
        
        cookies = self.load_cookies()
        if not cookies:
            print("❌ 未找到保存的 Cookie")
            return False
        
        print(f"📂 加载了 {len(cookies)} 条 Cookie")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            print(f"\n🌐 访问: {url[:60]}...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            # 检查登录状态
            is_logged_in = await self._verify_login(page)
            
            # 截图
            screenshot_path = OUTPUT_DIR / "session_test.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 截图: {screenshot_path}")
            
            await browser.close()
            
            if is_logged_in:
                print("\n✅ 会话有效！")
                self.session_info["is_valid"] = True
                self._save_session_info()
                return True
            else:
                print("\n❌ 会话已失效，需要重新登录")
                self.session_info["is_valid"] = False
                self._save_session_info()
                return False
    
    async def auto_refresh_if_needed(self):
        """如果需要则自动刷新会话"""
        if self.is_session_valid(max_age_hours=12):  # 12小时有效期
            print("✅ 会话仍然有效，无需刷新")
            return True
        
        print("⚠️ 会话已过期或即将过期，需要重新登录")
        return await self.interactive_login()


async def main():
    import sys
    
    manager = PersistentSessionManager()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 save_persistent_session.py login    # 交互式登录")
        print("  python3 save_persistent_session.py test     # 测试会话")
        print("  python3 save_persistent_session.py status   # 查看会话状态")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "login":
        success = await manager.interactive_login()
        sys.exit(0 if success else 1)
    
    elif command == "test":
        success = await manager.test_session()
        sys.exit(0 if success else 1)
    
    elif command == "status":
        print("=" * 70)
        print("📊 会话状态")
        print("=" * 70)
        print(f"Cookie 文件: {'✅ 存在' if COOKIE_FILE.exists() else '❌ 不存在'}")
        print(f"会话有效: {'✅ 是' if manager.is_session_valid() else '❌ 否'}")
        
        if manager.session_info["created_at"]:
            created = datetime.fromisoformat(manager.session_info["created_at"])
            print(f"创建时间: {created.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if manager.session_info["last_refresh"]:
            last = datetime.fromisoformat(manager.session_info["last_refresh"])
            print(f"最后刷新: {last.strftime('%Y-%m-%d %H:%M:%S')}")
            age = datetime.now() - last
            print(f"会话年龄: {age.total_seconds() / 3600:.1f} 小时")
        
        print(f"刷新次数: {manager.session_info.get('refresh_count', 0)}")
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
