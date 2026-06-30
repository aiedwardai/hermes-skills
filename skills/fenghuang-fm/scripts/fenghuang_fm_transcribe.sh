#!/usr/bin/env bash
# 凤凰FM 小爱晚报 — 下载音频 + AI转文字 + 结构化排版 + 第二大脑归档
# 用法: bash fenghuang_fm_transcribe.sh [pid] [date]
# 默认: pid=456498 (小爱晚报), date=今天

set -e

PID="${1:-456498}"
DATE="${2:-$(date +%Y-%m-%d)}"
UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36"
WIKI_DIR="${WIKI_PATH:-$HOME/wiki}"

echo "=== 凤凰FM 音频转文字 ==="
echo "PID: $PID | Date: $DATE"

# Step 1: 拉取节目列表
echo "[1/5] 拉取节目列表..."
curl -sL -A "$UA" \
  "https://d.fm.renbenai.com/fm/read/fmd/h5/getPayResourceList_714.html?pid=$PID&isFree=2&pageNum=1&callback=j" \
  -o /tmp/fm-list.json

# Step 2: 解析音频URL和元数据
echo "[2/5] 解析元数据..."
read -r AUDIO_URL TITLE DURATION PROGRAM_NAME <<< $(python3 -c "
import json, sys
with open('/tmp/fm-list.json') as f:
    raw = f.read()
d = json.loads(raw[raw.index('(')+1:raw.rindex(')')])
items = d['data']['list']
item = items[0]
print(item['audiolist'][0]['filePath'], item['title'], item.get('duration','?'), item.get('programName','小爱晚报'))
")

echo "  节目: $TITLE"
echo "  时长: ${DURATION}s"

# Step 3: 下载音频
echo "[3/5] 下载音频..."
curl -sL -o /tmp/xiaoi-latest.mp3 "$AUDIO_URL"
ls -lh /tmp/xiaoi-latest.mp3 | awk '{print "  大小: "$5}'

# Step 4: AI 转文字
echo "[4/5] AI 转写中..."
TRANSCRIPT=$(python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('base', device='cpu', compute_type='int8')
segs, info = m.transcribe('/tmp/xiaoi-latest.mp3', language='zh', beam_size=5)
print(''.join(s.text.strip() for s in segs))
")

# Step 5: 结构化排版 + 归档
echo "[5/5] 排版归档..."

# 计算分钟数
MINS=$((DURATION / 60))
SECS=$((DURATION % 60))

cat > "$WIKI_DIR/queries/fenghuang-xiaoi-${DATE}.md" << WIKIEOF
---
date: ${DATE}
title: 凤凰FM${PROGRAM_NAME} ${DATE}
tags: [fenghuang-fm, xiaoi, news, audio-transcript]
source: fenghuang-fm-pid${PID}
audio_url: ${AUDIO_URL}
transcribed: ${DATE}
---

# 📻 凤凰FM · ${PROGRAM_NAME} | ${DATE}

> 节目：${PROGRAM_NAME}（pid=${PID}）
> 时长：${MINS}分${SECS}秒
> 标题：${TITLE}
> 出品：人本智慧 · 凤凰FM
> 转写：faster-whisper (base)

---

## 完整转写文本

${TRANSCRIPT}

---

*自动转录 by Hermes Agent | 凤凰FM Skill v1.0*
WIKIEOF

echo "  ✓ 文件已保存: $WIKI_DIR/queries/fenghuang-xiaoi-${DATE}.md"

# Git 归档
cd "$WIKI_DIR"
git add "queries/fenghuang-xiaoi-${DATE}.md"
git commit -m "add: 凤凰FM${PROGRAM_NAME} ${DATE} 音频转文字" 2>/dev/null || true
git push 2>/dev/null || echo "  ⚠ git push 失败（可能无网络），本地文件已保存"

echo ""
echo "=== 完成 ==="
echo "$TRANSCRIPT" | head -c 500
echo "..."
