# DashScope ASR 配置

## API Key
```bash
export DASHSCOPE_API_KEY=sk-b70f29eb4e674f13ba76375625d3887a
```

## 模型选择

### 推荐模型
- **qwen-omni-turbo** ✅ 已验证可用
  - 支持音频/视频输入
  - 费用: ¥0.003/1K tokens (输入), ¥0.006/1K tokens (输出)
  - 约 ¥0.0005/次测试

### 其他模型
- **qwen3-omni-30b-a3b-captioner** ⚠️ 需要确认权限
  - 用户指定但未完全验证
  - 可能需要特殊调用格式或权限

## 使用方法

### 测试可用性
```bash
cd apps/api
python3 scripts/dashscope-asr.py test
```

### 转写音频/视频
```bash
# 使用默认模型 (qwen-omni-turbo)
python3 scripts/dashscope-asr.py "https://example.com/audio.mp3"

# 指定模型
python3 scripts/dashscope-asr.py "https://example.com/video.mp4" "qwen-omni-turbo"
```

## Node.js 集成

在 subtitle-extractor.ts 中，已将 ASR 兜底方案切换为 DashScope API。

无需额外配置，只需确保环境变量设置即可。

## 费用估算

| 视频时长 | Token数(估算) | 费用 |
|---------|--------------|------|
| 30秒 | ~300 | ¥0.001 |
| 1分钟 | ~600 | ¥0.002 |
| 5分钟 | ~3000 | ¥0.012 |

*比阿里云NLS ASR (¥2.5/小时 ≈ ¥0.04/分钟) 更便宜*

## 文档
- https://help.aliyun.com/document_detail/2712543.html
