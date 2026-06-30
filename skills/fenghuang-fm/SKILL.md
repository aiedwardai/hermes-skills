---
name: fenghuang-fm
description: 凤凰FM音频节目下载+AI转文字+排版归档。通过 JSONP API 拉取节目列表、下载 mp3、faster-whisper 转写中文、结构化排版、存档到第二大脑 Wiki。支持小爱晚报(pid=456498)及其他凤凰FM节目。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [audio, transcription, news, fenghuang, whisper, wiki]
    related_skills: [daily-intelligence, second-brain]
---

# 凤凰FM 音频转文字工作流

## 触发条件
- 用户提到"凤凰FM"、"小爱晚报"、"音频转文字"、"下载转写"
- 需要将凤凰FM节目内容纳入每日情报或第二大脑
- 用户提供凤凰FM的 pid 或节目名称

## 概述
凤凰FM（ifeng FM）是凤凰网旗下音频平台。本 skill 实现：
1. 通过 JSONP API 拉取节目列表
2. 下载最新一期 mp3 音频
3. faster-whisper AI 转写为中文文字
4. 结构化排版（按话题分段）
5. 归档到第二大脑 Wiki + git push

## 已知节目

| 节目名 | pid | 标签 | 更新状态 |
|--------|-----|------|---------|
| 小爱晚报 | 456498 | 热点新闻·每日新闻 | ✅ 每日更新 |

## 完整执行流程

### Step 1: 拉取节目列表

```bash
UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36"
curl -sL -A "$UA" \
  "https://d.fm.renbenai.com/fm/read/fmd/h5/getPayResourceList_714.html?pid=456498&isFree=2&pageNum=1&callback=j" \
  -o /tmp/fm-list.json
```

### Step 2: 解析音频URL和 Duration

```python
import json
with open('/tmp/fm-list.json') as f:
    raw = f.read()
json_str = raw[raw.index('(')+1:raw.rindex(')')]
d = json.loads(json_str)
items = d['data']['list']
latest = items[0]
audio_url = latest['audiolist'][0]['filePath']
duration = latest.get('duration', '?')
title = latest['title']
```

### Step 3: 下载音频

```bash
curl -sL -o /tmp/xiaoi-latest.mp3 "<audio_url>"
```

**注意**：音频域名 `p3.renbenzhihui.com` 需要服务器 DNS 可解析。

### Step 4: AI 转文字（faster-whisper）

```python
from faster_whisper import WhisperModel

model = WhisperModel('base', device='cpu', compute_type='int8')
segments, info = model.transcribe('/tmp/xiaoi-latest.mp3', language='zh', beam_size=5)

full_text = []
for segment in segments:
    text = segment.text.strip()
    if text:
        full_text.append(text)

result = ''.join(full_text)
```

**性能参考**：
- 500-750秒音频 → base模型CPU转写约 30-90 秒
- 中文新闻类内容识别准确率约 90%+

### Step 5: 结构化排版

将转写文本按话题分段，生成 Markdown 格式输出：

```markdown
---
date: YYYY-MM-DD
title: 凤凰FM小爱晚报 YYYY-MM-DD
tags: [fenghuang-fm, xiaoi, news, audio-transcript]
source: fenghuang-fm-pid456498
audio_url: <mp3_url>
transcribed: YYYY-MM-DD
---

# 📻 凤凰FM · 小爱晚报 | YYYY-MM-DD

> 节目：小爱晚报（pid=456498）
> 时长：X分X秒
> 出品：人本智慧 · 凤凰FM
> 转写：faster-whisper (base)

---

## 完整转写文本

时代新知 生活头条现在为您带来...

---

## 结构化摘要

**📌 头条要闻**
...

**💰 财经**
...

**⚽ 体育**
...

**📸 今日趣闻**
...

**💡 生活贴士**
...
```

### Step 6: 归档到第二大脑

```bash
# 保存文件
cat > ~/wiki/queries/fenghuang-xiaoi-YYYY-MM-DD.md << 'EOF'
<排版后的完整内容>
EOF

# Git commit + push
cd ~/wiki && git add queries/fenghuang-xiaoi-YYYY-MM-DD.md \
  && git commit -m "add: 凤凰FM小爱晚报 YYYY-MM-DD 音频转文字" \
  && git push
```

## 一键脚本

将以下脚本保存为 `~/.hermes/scripts/fenghuang_fm_transcribe.sh`：

```bash
#!/usr/bin/env bash
set -e

PID="${1:-456498}"
DATE=$(date +%Y-%m-%d)
UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36"

# Step 1: 拉取列表
curl -sL -A "$UA" \
  "https://d.fm.renbenai.com/fm/read/fmd/h5/getPayResourceList_714.html?pid=$PID&isFree=2&pageNum=1&callback=j" \
  -o /tmp/fm-list.json

# Step 2: 解析音频URL
AUDIO_URL=$(python3 -c "
import json
with open('/tmp/fm-list.json') as f:
    raw = f.read()
d = json.loads(raw[raw.index('(')+1:raw.rindex(')')])
items = d['data']['list']
print(items[0]['audiolist'][0]['filePath'])
")

TITLE=$(python3 -c "
import json
with open('/tmp/fm-list.json') as f:
    raw = f.read()
d = json.loads(raw[raw.index('(')+1:raw.rindex(')')])
items = d['data']['list']
print(items[0]['title'])
")

DURATION=$(python3 -c "
import json
with open('/tmp/fm-list.json') as f:
    raw = f.read()
d = json.loads(raw[raw.index('(')+1:raw.rindex(')')])
items = d['data']['list']
print(items[0].get('duration','?'))
")

# Step 3: 下载
echo "下载: $TITLE"
curl -sL -o /tmp/xiaoi-latest.mp3 "$AUDIO_URL"

# Step 4: 转文字
echo "转写中..."
TRANSCRIPT=$(python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('base', device='cpu', compute_type='int8')
segs, info = m.transcribe('/tmp/xiaoi-latest.mp3', language='zh', beam_size=5)
print(''.join(s.text.strip() for s in segs))
")

# Step 5: 输出
echo "=== 转写结果 ==="
echo "标题: $TITLE"
echo "时长: ${DURATION}s"
echo "音频: $AUDIO_URL"
echo "==="
echo "$TRANSCRIPT"

# Step 6: 存档
WIKI_FILE="$HOME/wiki/queries/fenghuang-xiaoi-${DATE}.md"
cat > "$WIKI_FILE" WIKIEOF
---
date: ${DATE}
title: 凤凰FM小爱晚报 ${DATE}
tags: [fenghuang-fm, xiaoi, news, audio-transcript]
source: fenghuang-fm-pid${PID}
audio_url: ${AUDIO_URL}
transcribed: ${DATE}
---

# 📻 凤凰FM · 小爱晚报 | ${DATE}

> 程序：小爱晚报（pid=${PID}）
> 时长：${DURATION}s
> 出品：人本智慧 · 凤凰FM
> 转写：faster-whisper (base)

## 完整转写文本

${TRANSCRIPT}
WIKIEOF

cd "$HOME/wiki"
git add "queries/fenghuang-xiaoi-${DATE}.md"
git commit -m "add: 凤凰FM小爱晚报 ${DATE}" 2>/dev/null || true
git push 2>/dev/null || true

echo "已归档: $WIKI_FILE"
```

```bash
chmod +x ~/.hermes/scripts/fenghuang_fm_transcribe.sh
```

### 使用方式
```bash
# 转写最新一期（默认小爱晚报）
bash ~/.hermes/scripts/fenghuang_fm_transcribe.sh

# 指定其他 pid
bash ~/.hermes/scripts/fenghuang_fm_transcribe.sh 456496
```

## 批量回补历史节目

```bash
# 连续回补最近 N 天
for i in $(seq 1 7); do
  DATE=$(date -d "$i days ago" +%Y-%m-%d)
  # 手动指定日期...
done
```

## 依赖

| 依赖 | 安装命令 | 说明 |
|------|---------|------|
| faster-whisper | `pip install faster-whisper` | ASR 语音转文字（已安装） |
| curl | 预置 | 下载音频 |
| Python 3.11+ | 预置 | JSON 解析 |

## API 接口详情
详见 `references/fenghuang-fm-api.md`

## 注意事项
- 必须带移动端 UA（Android Chrome）
- 返回 JSONP（`j({...})`）需去掉回调包装
- 音频域名 `p3.renbenzhihui.com` 需 DNS 可解析（境外服务器可能无法访问）
- base 模型对中文新闻识别较好，但可能有人名/专有名词误差
- 转写完成后建议人工校对关键信息

## 与每日情报集成
此 skill 可作为每日情报 cron（18:00）的数据源 #10：
```markdown
10. 凤凰FM/小爱晚报（pid=456498）— 音频下载+转文字：
    a. 执行 fenghuang_fm_transcribe.sh
    b. 转写结果纳入日报"国内新闻"板块
    c. 标注来源：🔗 [凤凰FM·小爱晚报](音频URL)
```
