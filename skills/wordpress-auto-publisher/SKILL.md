---
name: wordpress-auto-publisher
description: "自动审阅并发布内容到 token2x.com WordPress 站点（Cloudflare CDN + Wordfence）。使用 REST API + Application Password 认证，自动处理分类、标签、slug 优化、图片上传。"
version: 1.1.0
author: hermes-agent
platforms: [linux, macos]
metadata:
  hermes:
    tags: [WordPress, Publishing, Cloudflare, REST-API, Images]
---

# WordPress Auto Publisher (token2x.com)

自动将内容（转载文章、报告、简报等）发布到 https://www.token2x.com WordPress 站点。

## 站点信息

| 项目 | 值 |
|------|-----|
| 站点URL | `https://www.token2x.com` |
| API端点 | `https://www.token2x.com/wp-json/wp/v2/` |
| 用户名 | `Edwardai` |
| 认证方式 | Application Password (Basic Auth)，通过环境变量传入 |
| CDN | Cloudflare |
| 安全插件 | Wordfence（已允许应用密码） |

## 凭证安全

**⚠️ 重要：发布到公开仓库时，不要暴露密码！**

所有 curl 示例和脚本已改用环境变量占位符 `$WP_USER` 和 `$WP_APP_PASSWORD`。使用时先设置：

```bash
export WP_USER=Edwardai
export WP_APP_PASSWORD="你的应用密码"
```

凭证信息存储在 Hermes memory 中，新会话自动加载。如需在配置文件持久化，使用 `hermes config set` 设置环境变量而非直接写入密码。

## 分类体系

| ID | 名称 | 用途 | Slug |
|----|------|------|------|
| 7 | JianInsight（剑识） | 分析评论、深度观点 | `%e5%89%91%e8%af%86` |
| 10 | JianNews（剑闻） | 资讯汇总、转载新闻 | `news` |
| 12 | 《Tokenology》V1.0 | Tokenology系列 | `tokenologyv1` |
| 13 | 《Tokenology》v2.0 | Tokenology系列 | `tokenology2` |
| 15 | MetaOne | MetaOne系列 | `metaone` |

## 发布工作流

### 1. 内容准备
- 从原文提取完整内容（文本 + 图片）
- 整理成结构化 HTML
- 添加原文来源链接和归属

### 2. 分类选择
- **新闻/资讯/转载** → JianNews (ID 10)
- **分析评论/深度观点** → JianInsight (ID 7)
- **系列连载** → 对应的 Tokenology/MetaOne 分类

### 3. API 发布命令模板

```bash
# 创建文章
curl -s -X POST \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  'https://www.token2x.com/wp-json/wp/v2/posts' \
  -H 'Content-Type: application/json' \
  -d @/tmp/wp_post.json

# 更新文章（修改slug、内容等）
curl -s -X POST \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  'https://www.token2x.com/wp-json/wp/v2/posts/{post_id}' \
  -H 'Content-Type: application/json' \
  -d @/tmp/wp_update.json

# 获取分类列表
curl -s -u "$WP_USER:$WP_APP_PASSWORD" \
  'https://www.token2x.com/wp-json/wp/v2/categories?per_page=100'

# 获取最新文章
curl -s -u "$WP_USER:$WP_APP_PASSWORD" \
  'https://www.token2x.com/wp-json/wp/v2/posts?per_page=5&_fields=id,link,title,status,date,categories'
```

### 4. JSON 数据结构

```json
{
  "title": "文章标题",
  "content": "<h2>章节标题</h2><p>段落内容</p>",
  "status": "publish",
  "categories": [10],
  "slug": "english-friendly-slug"
}
```

### 5. 发布后验证
- 通过 API 获取文章的 `link` 字段确认发布
- 确保返回的 `status` 为 `"publish"`
- 检查 slug 是否为英文友好格式（如有必要，用 POST 更新）

### ⚠️ 陷阱: content.raw 为空
用 `GET /posts/{id}` 时，如果不加 `?edit=true`，`content.raw` 可能为空。所以：
- **更新内容**时：直接用 POST 写入完整的 `content` 字段即可，不要先 GET 再追加
- **读取旧内容**时：必须加 `?edit=true` 参数
- 如果不小心用空内容更新了文章，重新 POST 完整内容即可恢复

## 图片上传流程

### 微信图片下载
微信文章图片托管在 `mmbiz.qpic.cn`，有防盗链保护。下载时需加 Referer header：
```bash
curl -s -o /tmp/img.jpg \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
  -H 'Referer: https://mp.weixin.qq.com/' \
  'https://mmbiz.qpic.cn/...' \
  --connect-timeout 15 --max-time 30
```

### 上传到 WordPress 媒体库
```bash
curl -s -X POST -u "$WP_USER:$WP_APP_PASSWORD" \
  'https://www.token2x.com/wp-json/wp/v2/media' \
  -F 'file=@/tmp/img.jpg;type=image/jpeg' \
  --connect-timeout 15 --max-time 30
```
返回数据中包含 `id` 和 `source_url`（即 WordPress 上的新URL）。

### 替换文章中的图片URL
下载上传后，原URL替换为新URL，重新 POST 更新文章。

### 备用脚本

技能内置脚本 `scripts/wordpress-upload-images.py` 封装了上述三步流程：

```bash
# 先设置凭证
export WP_USER=Edwardai WP_APP_PASSWORD="你的应用密码"

# 从技能目录调用脚本
python3 ~/.hermes/skills/publishing/wordpress-auto-publisher/scripts/wordpress-upload-images.py <post_id> <url1> <url2> ...

# 或通过单行环境变量传参
WP_USER=Edwardai WP_APP_PASSWORD="密码" python3 scripts/wordpress-upload-images.py <post_id> <url1>
```

## 微信文章图片获取方案对比

转载微信文章到 WordPress 时，获取图片有三级方案：

### Tier 1: 浏览器直接拿（最简单，本文可行吗？）
打开文章页面 → 浏览器渲染 → 提取 `<img>` 标签的 data-src/src。

**现状**：微信文章页面 DOM 被沙箱化，浏览器能显示内容但 JS 无法访问 DOM 树。本方案对微信文章**不可行**。

### Tier 2: 微信开放平台 API（最可靠，需授权）
调用微信公众号素材管理接口，直接获取结构化文章数据：

```
POST https://api.weixin.qq.com/cgi-bin/material/get_material
Body: {"media_id": "文章的素材ID"}
返回: {
  "content": "<完整的文章HTML>",
  "news_item": [{...}]
}
```

**条件**（必须全部满足）：
1. 文章所属公众号的 **AppID + AppSecret**
2. 该文章的 **media_id**（素材ID）
3. Hermes 服务器IP添加进该公众号后台的 **IP白名单**

**适用范围**：
- 自己的公众号（如 剑胆琴新）：你有 AppID+Secret，只需加IP白名单
- 第三方公众号（如 易全联）：需要对方配合提供凭据

### Tier 3: 手动处理（保底方案）
- 从原文逐张截图保存
- 或联系作者获取原图
- 上传到 WordPress 媒体库

### 当前推荐策略
转载第三方文章时：
- **封面图**：微信URL加Referer可下载，直接上传使用
- **正文图**：如果拿不到完整URL，保留文字+原文链接，引导读者去原文看图
- **自创内容**：本地图片直接上传

## 内容更新注意事项

### 更新内容的正确做法
```python
# ✅ 正确：直接写完整内容
data = json.dumps({
    "content": "<p>完整HTML内容</p>",
    "status": "publish"
})
curl -X POST -u '用户:密码' \
  'https://www.token2x.com/wp-json/wp/v2/posts/{id}' \
  -d @content.json

# ❌ 错误：先GET content.raw（不加edit=true时空值）再追加
current = GET /posts/{id}  # content.raw可能为空
data = current + new_content  # 可能会覆盖为只有new_content
```

### REST API 参数
- GET 文章时加 `?edit=true` 才能获取 `content.raw`
- POST 更新时不需要 `edit=true`，直接传完整 content

## 注意事项

### Cloudflare
- Cloudflare CDN 不阻止 REST API 调用（直接走源站API）
- 文章发布后可能因缓存有短暂延迟，刷新即可看到

### Wordfence
- 已配置允许 Application Password 认证
- 如果遇到 403 错误，检查 Wordfence 速率限制

### 标题策略
- 转载文章保留核心信息，可适当优化标题长度
- 剑闻类（新闻）：直接简明扼要
- 剑识类（观点）：保留核心观点冲击力

## 安全提醒
- 应用密码在 memory 中存储，不要写在公开回复里
- 每次用 `@/tmp/wp_post.json` 文件传数据，避免 shell 转义问题