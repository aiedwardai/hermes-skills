# 凤凰FM API 数据源

## 发现日期
2026-06-28

## 更新记录
- 2026-06-30 — 新增音频下载 + faster-whisper 转文字流程，已集成到每日情报 cron

## 概述
凤凰FM（ifeng FM）是凤凰网旗下的音频平台，提供新闻类音频节目。通过逆向其移动端 JS 代码发现 JSONP API，可直接获取节目元数据和音频列表。

## 已知节目

| 节目名 | pid | 类型 | 更新频率 |
|--------|-----|------|---------|
| 小爱晚报 | 456498 | 每日新闻 | 每日 |

## API 接口

### 1. 节目元数据
```
GET https://s.fm.renbenai.com/fm/read/{pid}_BackData/getProgramData.html
User-Agent: Android Chrome (必须)
```
返回 JSONP（`j({...})`），包含：
- `programName` — 节目名称
- `programDetails` — 节目简介
- `tags` — 标签
- `ratingStar` — 评分
- `newestResource` — 最新一期信息（含标题、发布时间、音频URL）

### 2. 节目列表
```
GET https://d.fm.renbenai.com/fm/read/fmd/h5/getPayResourceList_714.html?pid={pid}&isFree=2&pageNum=1&callback=j
User-Agent: Android Chrome (必须)
```
返回 JSONP，包含：
- `data.list[]` — 节目列表
  - `.title` — 节目标题（含日期，如"6月28日小爱晚报：xxx"）
  - `.audiolist[0].filePath` — 音频直链（.mp3），域名 p3.renbenzhihui.com
  - `.publishTime` — 发布时间
  - `.duration` — 时长（秒）

### 3. 获取示例
```bash
# 节目信息
curl -sL -A "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36" \
  "https://s.fm.renbenai.com/fm/read/456498_BackData/getProgramData.html"

# 节目列表
curl -sL -A "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36" \
  "https://d.fm.renbenai.com/fm/read/fmd/h5/getPayResourceList_714.html?pid=456498&isFree=2&pageNum=1&callback=j"
```

## 音频转文字（ASR）完整流程

### 依赖
- `faster-whisper` 已安装（pip install faster-whisper）
- 模型：`base`（int8 量化，CPU 可用，中文识别基本可用）

### 步骤

```bash
# Step 1: 拉取节目列表
curl -sL -A "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36" \
  "https://d.fm.renbenai.com/fm/read/fmd/h5/getPayResourceList_714.html?pid=456498&isFree=2&pageNum=1&callback=j" \
  -o /tmp/fm-list.json

# Step 2: 提取最新音频URL
AUDIO_URL=$(python3 -c "
import json
with open('/tmp/fm-list.json') as f:
    d = json.load(f)
items = d['data']['list']
print(items[0]['audiolist'][0]['filePath'])
")

# Step 3: 下载音频
curl -sL -o /tmp/xiaoi-latest.mp3 "$AUDIO_URL"

# Step 4: 转文字
python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('base', device='cpu', compute_type='int8')
segs, info = m.transcribe('/tmp/xiaoi-latest.mp3', language='zh', beam_size=5)
print(''.join(s.text.strip() for s in segs))
"
```

### 性能参考
- 小爱晚报约 500-750 秒音频
- base 模型在 CPU 上转写约需 30-90 秒
- 中文识别准确率：新闻类内容约 90%+

## 注意事项
- 必须带移动端 User-Agent，否则可能被拒绝
- 返回格式是 JSONP（`j({...})`），需要去掉回调包装再解析 JSON（注意：不是 `BackData`，是 `j`）
- 音频直链可直接下载 .mp3 文件
- 节目标题格式：`{月}{日}小爱晚报：{新闻摘要}`，可直接提取当日新闻标题
- 音频域名 p3.renbenzhihui.com 需要 DNS 能解析（部分境外服务器可能无法访问）

## 用途
- 每日新闻数据源（音频转文字后纳入日报）
- 标题可用于剑闻素材池的"国内新闻"板块
- 转写文字自动存档到第二大脑 Wiki

## 第二大脑存档
- 路径：`~/wiki/queries/fenghuang-xiaoi-YYYY-MM-DD.md`
- 格式：YAML frontmatter + 结构化摘要 + 完整转写文本
