#!/bin/bash
# 火山引擎 TTS 独立脚本 v2 (V3 API)
# 用法: ./volcengine_tts.sh "要朗读的文字" [输出文件名.mp3]
#
# 前置条件: VOLC_TTS_API_KEY + VOLC_TTS_VOICE_ID 在 ~/.hermes/.env 中

set -e

TEXT="${1:?错误: 请提供要朗读的文字}"
OUTPUT="${2:-output.mp3}"
REQID="TTS_$(date +%s)_$(shuf -i 1000-9999 -n 1)"

# 加载 .env
set -a; source ~/.hermes/.env; set +a
: "${VOLC_TTS_API_KEY:?错误: VOLC_TTS_API_KEY 未设置}"
: "${VOLC_TTS_VOICE_ID:?错误: VOLC_TTS_VOICE_ID 未设置}"

echo "📝 正在合成语音..."
echo "   文字: ${TEXT:0:60}..."
echo "   输出: $OUTPUT"

# V3 API - 流式分块返回，需要拼接
python3 << PYEOF
import json, base64, urllib.request, os, uuid

api_key = os.environ.get('VOLC_TTS_API_KEY', '')
voice_id = os.environ.get('VOLC_TTS_VOICE_ID', '')
text = """$TEXT"""
reqid = str(uuid.uuid4())

payload = {
    "req_params": {
        "text": text,
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
        "X-Api-Request-Id": reqid,
        "Content-Type": "application/json"
    },
    method="POST"
)

resp = urllib.request.urlopen(req, timeout=30)
raw = resp.read().decode('utf-8')
audio_parts = []
for line in raw.strip().split('\n'):
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
    except:
        continue
    code = data.get('code', -1)
    if code == 0:
        chunk = data.get('data', '')
        if chunk:
            audio_parts.append(chunk)

if audio_parts:
    full_audio = base64.b64decode(''.join(audio_parts))
    with open("$OUTPUT", 'wb') as f:
        f.write(full_audio)
    print(f'✓ 已生成: $OUTPUT')
    print(f'  大小: {len(full_audio)/1024:.1f} KB')
else:
    print('✗ 无音频数据返回')
    exit(1)
PYEOF