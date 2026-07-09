---
name: vtts
description: 使用火山引擎（字节跳动）TTS API V3 生成语音，支持复刻音色和标准音色
category: voice
tags: [tts, volcengine, voice-clone, bytedance]
---

# 火山引擎 TTS 配音（V3 API）

使用火山引擎 **V3 API** (`/api/v3/tts/unidirectional`) 将文字转为语音 MP3，支持用户自己的克隆音色和标准音色。

## 前置条件

- API Key 和 Voice ID 保存在 `~/.hermes/.env` 中：
  ```bash
  VOLC_TTS_API_KEY=your_api_key      # 从火山引擎控制台获取
  VOLC_TTS_VOICE_ID=your_voice_id     # 复刻音色 ID 或标准音色名
  ```
- 国内网络环境（`openspeech.bytedance.com` 直连）

## 与旧版 V1 API 的区别

| 维度 | V1（旧） | V3（当前） |
|------|---------|-----------|
| 端点 | `/api/v1/tts` | `/api/v3/tts/unidirectional` |
| 模型标识 | `cluster: volcano_icl` | `X-Api-Resource-Id: seed-icl-2.0` |
| 请求 ID | 时间戳+随机数 | `X-Api-Request-Id: UUID` |
| 请求体 | `app/user/audio/request` 嵌套 | `req_params{text, speaker, audio_params}` 扁平 |
| 返回格式 | `code==3000` 成功 | `code==0` 成功 |
| 推荐状态 | ⛔ 不推荐 | ✅ 官方推荐 |

## 技能用法

⚠️ 每次开始前，先展示当前配置和默认参数，等用户确认后再执行。

### 生成语音文件（V3 API，流式分块返回）

```python
import json, base64, uuid, urllib.request, os

api_key = os.environ['VOLC_TTS_API_KEY']
voice_id = os.environ['VOLC_TTS_VOICE_ID']

payload = {
    "req_params": {
        "text": "要朗读的文字内容",
        "speaker": voice_id,
        "audio_params": {"format": "mp3", "sample_rate": 24000}
    }
}

req = urllib.request.Request(
    "https://openspeech.bytedance.com/api/v3/tts/unidirectional",
    data=json.dumps(payload).encode('utf-8'),
    headers={
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": "seed-icl-2.0",
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json"
    },
    method="POST"
)

resp = urllib.request.urlopen(req, timeout=15)
raw = resp.read().decode('utf-8')

# V3 API 返回流式分块 JSON（每行一个 JSON 对象）
audio_parts = []
for line in raw.strip().split('\n'):
    line = line.strip()
    if not line: continue
    try:
        data = json.loads(line)
    except: continue
    if data.get('code') == 0:
        chunk = data.get('data', '')
        if chunk:
            audio_parts.append(chunk)

if audio_parts:
    audio = base64.b64decode(''.join(audio_parts))
    with open('output.mp3', 'wb') as f:
        f.write(audio)
    print(f"✓ 已生成: output.mp3 ({len(audio)/1024:.1f} KB, {len(audio_parts)} chunks)")
else:
    print(f"✗ 无音频数据")
```

### 独立脚本

```bash
bash ~/.hermes/scripts/volcengine_tts.sh "要朗读的文字" output.mp3
```

## 参数说明

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `speaker` | 音色 ID | 来自控制台音色库 |
| `format` | 音频编码 | mp3 / wav / pcm / ogg_opus |
| `sample_rate` | 采样率 | 8000 / 16000 / 24000 |
| `X-Api-Resource-Id` | 模型版本 | `seed-tts-2.0`（标准）/ `seed-icl-2.0`（复刻） |

可选参数：`speed_ratio`(0.1-2.0), `pitch`(-12~12), `volume_ratio`(0.1-3.0)

## 注意事项

- **V1 API 已不推荐**：请使用 V3 API
- **不要硬编码 Key**：API Key 必须从 `.env` 环境变量读取
- **API Key 必须从控制台获取**：登录火山引擎控制台 → 语音技术 → API Key管理
- **不要用 `-o` 直接保存**：API 返回 JSON，需 base64 解码 data 字段
- **复刻音色用 `seed-icl-2.0`**，标准音色用 `seed-tts-2.0`
- **`X-Api-Request-Id` 必须是 UUID**

## 常见坑点

- ❌ **使用旧 V1 API 端点和请求格式导致 401/403** → 改用 V3 API
- ❌ **请求体用了 V1 的 `app/user/audio/request` 格式** → V3 用 `req_params` 扁平格式
- ❌ **`-o output.mp3` 保存 JSON 到 MP3 文件** → 必须 base64 解码 data 字段
- ❌ **`set -a` 没加导致环境变量不生效** → `source .env` 前必须 `set -a`