
import os
import json
import base64
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

RSS_FEEDS = {
    "BBC Bangla": "https://feeds.bbci.co.uk/bengali/rss.xml",
    "Google News Bangladesh": (
        "https://news.google.com/rss/search?"
        "q=Bangladesh&hl=bn&gl=BD&ceid=BD:bn"
    ),
}

WP_URL = os.environ["WP_URL"].rstrip("/")
WP_USERNAME = os.environ["WP_USERNAME"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]


def wp_request(url, data=None):
    credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()
    token = base64.b64encode(credentials).decode()

    headers = {
        "Authorization": f"Basic {token}",
        "User-Agent": "DailyBanglaNews/1.0",
    }

    if data is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST" if data is not None else "GET",
    )

   with urllib.request.urlopen(request, timeout=30) as response:
    raw = response.read()
    print("WordPress HTTP Status:", response.status)
    print("Response Content-Type:", response.headers.get("Content-Type"))
    print("Response Preview:", raw[:200])
    return json.loads(raw.decode("utf-8-sig"))


def create_draft(title, link, source):
    query = urllib.parse.urlencode({"search": title})
    check_url = f"{WP_URL}/wp-json/wp/v2/posts?{query}"

    posts = wp_request(check_url)

    for post in posts:
        existing_title = post.get("title", {}).get("rendered", "")
        if existing_title.strip().lower() == title.strip().lower():
            print("Already exists:", title)
            return

    content = (
        "<p>মূল সংবাদটি পড়ুন:</p>"
        f'<p><a href="{link}">{source} - মূল সংবাদ</a></p>'
    )

    post_data = json.dumps({
        "title": title,
        "content": content,
        "status": "draft",
    }).encode("utf-8")

    result = wp_request(
        f"{WP_URL}/wp-json/wp/v2/posts",
        data=post_data,
    )

    print("DRAFT CREATED:", result.get("id"), title)


def collect_news():
    print("Daily Bangla News - WordPress Draft Test")

    for source, feed_url in RSS_FEEDS.items():
        print("Checking:", source)

        request = urllib.request.Request(
            feed_url,
            headers={"User-Agent": "DailyBanglaNews/1.0"},
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            root = ET.fromstring(response.read())

        items = root.findall(".//item")

        for item in items:
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()

            if title and link:
                create_draft(title, link, source)
                return

    print("No news found.")


if __name__ == "__main__":
    collect_news()
