# 阿里云 ASR 接入指南

## 功能说明

当抖音视频**没有自动字幕**时，系统会自动使用阿里云语音识别服务进行转写。

**流程**:
```
1. API拦截提取自动字幕
   ├── 有字幕 → 返回字幕
   └── 无字幕 → 步骤2

2. 获取音频URL
   └── 调用 extract-full.py audio_only

3. 阿里云ASR转写
   └── 返回转写文本
```

**费用**: ¥2.5/小时，约 **¥0.04/分钟视频**

---

## 接入步骤

### 1. 开通阿里云智能语音交互

访问: https://www.aliyun.com/product/nls

1. 登录阿里云账号
2. 点击「立即开通」
3. 选择「录音文件识别」服务

### 2. 创建项目获取 AppKey

1. 进入控制台: https://nls-portal.console.aliyun.com/
2. 点击「创建项目」
3. 项目名称: `auto-home-media`
4. 服务类型: 选择「录音文件识别」
5. 保存 **AppKey**

### 3. 获取 AccessKey

1. 访问: https://ram.console.aliyun.com/manage/ak
2. 点击「创建 AccessKey」
3. 保存 **AccessKey ID** 和 **AccessKey Secret**
4. ⚠️ **安全提示**: 不要泄露 AK/SK，建议创建子账号并赋予最小权限

### 4. 配置环境变量

```bash
# 添加到 ~/.zshrc 或 ~/.bash_profile
export ALIYUN_ACCESS_KEY_ID=your_access_key_id
export ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
export ALIYUN_APP_KEY=your_app_key

# 使配置生效
source ~/.zshrc
```

### 5. 安装阿里云 Python SDK

```bash
pip3 install aliyun-python-sdk-core --break-system-packages
```

### 6. 测试接入

```bash
cd apps/api

# 测试获取音频URL
python3 scripts/extract-full.py "https://v.douyin.com/xxxxx/" audio_only

# 测试阿里云ASR（需要配置AK后）
python3 scripts/aliyun-asr-sdk.py "音频URL"

# 测试完整流程
npx tsx scripts/test-subtitle.ts "https://v.douyin.com/xxxxx/"
```

---

## 文件说明

| 文件 | 作用 |
|------|------|
| `scripts/aliyun-asr-sdk.py` | 阿里云ASR Python SDK调用 |
| `scripts/extract-full.py` | 完整提取（含音频URL获取） |
| `src/services/subtitle-extractor.ts` | Node.js服务集成 |
| `src/services/aliyun-asr.ts` | 阿里云ASR服务模块 |

---

## 费用估算

| 视频时长 | 费用 |
|---------|------|
| 30秒 | ¥0.02 |
| 1分钟 | ¥0.04 |
| 5分钟 | ¥0.21 |
| 10分钟 | ¥0.42 |

**新用户优惠**:
- 阿里云提供一定免费额度
- 具体查看: https://www.aliyun.com/price/product#/nls/overview

---

## 故障排查

### 问题1: "阿里云配置不完整"
**解决**: 检查环境变量是否设置正确
```bash
echo $ALIYUN_ACCESS_KEY_ID
echo $ALIYUN_APP_KEY
```

### 问题2: "获取音频URL失败"
**解决**: 检查cookies是否有效
```bash
python3 scripts/extract-full.py "视频URL" audio_only
```

### 问题3: 阿里云SDK未安装
**解决**: 
```bash
pip3 install aliyun-python-sdk-core --break-system-packages
```

---

## 替代方案

如果阿里云接入复杂，可考虑：

| 方案 | 费用 | 接入难度 |
|------|------|---------|
| 阿里云ASR | ¥2.5/小时 | 中 |
| 讯飞听见 | ¥0.33/分钟 | 低 |
| 本地Whisper | 免费 | 高（需要GPU） |
| 手动录入 | 免费 | - |

---

## 技术支持

- 阿里云文档: https://help.aliyun.com/document_detail/90728.html
- 项目Issues: https://github.com/xzpo-Jack-ai/Auto-home-sale-media-creator/issues
