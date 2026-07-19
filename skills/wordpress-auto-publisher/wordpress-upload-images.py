#!/usr/bin/env python3
"""
wordpress-upload-images.py — WordPress 图片上传工具

下载原文图片 → 上传到 WordPress 媒体库 → 更新文章内容

用法:
  python3 wordpress-upload-images.py <post_id> <image_url> [image_url2 ...]
  python3 wordpress-upload-images.py <post_id> --from-file urls.txt

环境变量:
  WP_USER — WordPress 用户名 (默认: Edwardai)
  WP_APP_PASSWORD — WordPress 应用密码
  WP_SITE_URL — WordPress 站点URL (默认: https://www.token2x.com)

需要安装: requests (pip install requests)
"""

import os
import sys
import json
import tempfile
import mimetypes
import urllib.request
import urllib.parse

# ── 配置 ──────────────────────────────────────────────
WP_USER = os.environ.get("WP_USER", "Edwardai")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")
WP_SITE_URL = os.environ.get("WP_SITE_URL", "https://www.token2x.com")
WP_API = f"{WP_SITE_URL}/wp-json/wp/v2"

# ── 辅助函数 ─────────────────────────────────────────

def get_wordpress_auth():
    """Return configured WordPress credentials without embedding secrets."""
    if not WP_APP_PASSWORD:
        raise RuntimeError("WP_APP_PASSWORD environment variable is required")
    return WP_USER, WP_APP_PASSWORD


def wp_request(method, endpoint, **kwargs):
    """向 WordPress REST API 发请求"""
    import requests
    url = f"{WP_API}/{endpoint.lstrip('/')}"
    auth = get_wordpress_auth()
    headers = kwargs.pop("headers", {})
    if "Content-Type" not in headers and "data" not in kwargs and "files" not in kwargs:
        headers["Content-Type"] = "application/json"

    resp = requests.request(
        method, url, auth=auth, headers=headers,
        timeout=30, **kwargs
    )
    resp.raise_for_status()
    return resp.json()


def download_image(url, ref_name=None):
    """下载图片到临时文件，返回本地路径"""
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://mp.weixin.qq.com/",
    }
    resp = requests.get(url, headers=headers, timeout=30, stream=True)
    resp.raise_for_status()

    # 确定扩展名
    content_type = resp.headers.get("Content-Type", "")
    ext_map = {
        "image/jpeg": ".jpg", "image/jpg": ".jpg",
        "image/png": ".png", "image/gif": ".gif",
        "image/webp": ".webp", "image/svg+xml": ".svg",
    }
    ext = ext_map.get(content_type, "")
    if not ext:
        # 从URL推断
        parsed = urllib.parse.urlparse(url)
        path_ext = os.path.splitext(parsed.path)[1]
        if path_ext:
            ext = path_ext
        else:
            ext = ".jpg"  # 默认

    suffix = f"{ref_name or 'image'}{ext}"
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return path, content_type


def upload_to_wordpress(local_path, content_type=None, filename=None):
    """上传本地图片到 WordPress 媒体库，返回媒体对象"""
    import requests

    if not filename:
        filename = os.path.basename(local_path)
    if not content_type:
        content_type, _ = mimetypes.guess_type(local_path)
        if not content_type:
            content_type = "image/jpeg"

    url = f"{WP_API}/media"
    auth = get_wordpress_auth()

    with open(local_path, "rb") as f:
        files = {"file": (filename, f, content_type)}
        resp = requests.post(url, auth=auth, files=files, timeout=60)

    resp.raise_for_status()
    data = resp.json()
    return {
        "id": data["id"],
        "url": data.get("source_url") or data["guid"]["rendered"],
        "title": data.get("title", {}).get("rendered", filename),
    }


def update_post_content(post_id, new_content):
    """更新文章的 HTML 内容"""
    data = json.dumps({
        "content": new_content,
        "status": "publish",
    })
    import requests
    url = f"{WP_API}/posts/{post_id}"
    auth = get_wordpress_auth()
    resp = requests.post(url, auth=auth, headers={"Content-Type": "application/json"}, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_post(post_id):
    """获取文章内容"""
    return wp_request("GET", f"posts/{post_id}")


# ── 主流程 ───────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    post_id = sys.argv[1]

    # 收集图片URL
    image_urls = []
    if sys.argv[2] == "--from-file" and len(sys.argv) >= 4:
        with open(sys.argv[3]) as f:
            image_urls = [line.strip() for line in f if line.strip()]
    else:
        image_urls = sys.argv[2:]

    if not image_urls:
        print("❌ 没有提供图片URL")
        sys.exit(1)

    print(f"📦 文章ID: {post_id}")
    print(f"🖼️  待处理图片: {len(image_urls)} 张")

    # 获取当前文章内容
    print("📖 获取当前文章...")
    post = get_post(post_id)
    content = post["content"]["raw"]
    print(f"  标题: {post['title']['raw']}")
    print(f"  内容长度: {len(content)} 字符")

    # 逐张下载→上传→替换
    for i, url in enumerate(image_urls):
        url = url.strip()
        if not url:
            continue
        print(f"\n[{i+1}/{len(image_urls)}] 处理: {url[:80]}...")

        try:
            # 下载
            local_path, content_type = download_image(url, ref_name=f"img{i}")
            file_size = os.path.getsize(local_path)
            print(f"  📥 下载完成: {file_size/1024:.1f}KB → {local_path}")

            # 上传
            media = upload_to_wordpress(local_path, content_type, f"img{i}")
            wp_url = media["url"]
            print(f"  📤 上传成功: ID={media['id']}, URL={wp_url}")

            # 替换内容中的原URL
            # 尝试多种格式
            old_url_variants = [
                url,
                url.replace("https://", "//"),
                url.replace("http://", "//"),
                url.replace("https://", "http://"),
            ]
            replaced = False
            for old_url in old_url_variants:
                if old_url in content:
                    content = content.replace(old_url, wp_url)
                    print(f"  🔄 替换 URL: {old_url[:50]}... → {wp_url[:50]}...")
                    replaced = True
                    break

            if not replaced:
                print(f"  ⚠️  未在文章内容中找到该URL，追加图片到文末")
                content += f'\n<p><img src="{wp_url}" alt="" /></p>'

            # 清理临时文件
            os.unlink(local_path)

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            continue

    # 更新文章
    print(f"\n🔄 更新文章内容...")
    updated = update_post_content(post_id, content)
    print(f"✅ 更新完成!")
    print(f"  链接: {updated['link']}")


if __name__ == "__main__":
    main()
