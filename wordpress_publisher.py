import os
import json
import base64
import html
import urllib.request
import urllib.error
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
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"].replace(" ", "")


def wp_request(url, data=None):

    credentials = (
        f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    ).encode("utf-8")

    token = base64.b64encode(credentials).decode("ascii")

    headers = {
        "Authorization": f"Basic {token}",
        "User-Agent": "DailyBanglaNews/1.0",
        "Accept": "application/json",
    }

    if data is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST" if data is not None else "GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()

            print("WordPress HTTP Status:", response.status)
            print("Response Content-Type:",
                  response.headers.get("Content-Type"))

            if not raw.strip():
                raise RuntimeError("Empty WordPress response")

            return json.loads(raw.decode("utf-8-sig"))

    except urllib.error.HTTPError as error:
        print("WordPress HTTP Error:", error.code)
        print(
            "Error Details:",
            error.read(1000).decode("utf-8", errors="replace")
        )
        raise


def already_exists(title):

    query = urllib.parse.urlencode({
        "search": title,
        "per_page": 100,
        "status": "draft,publish,pending,private",
    })

    url = f"{WP_URL}/wp-json/wp/v2/posts?{query}"

    posts = wp_request(url)

    for post in posts:
        existing = html.unescape(
            post.get("title", {}).get("rendered", "")
        ).strip().lower()

        if existing == title.strip().lower():
            print("Duplicate skipped:", title)
            return True

    return False


def create_draft(title, link, source):

    if already_exists(title):
        return False

    safe_link = html.escape(link, quote=True)
    safe_source = html.escape(source)

    content = (
        "<p>এই সংবাদটি মূল সংবাদসূত্র থেকে সংগৃহীত। "
        "প্রকাশের আগে তথ্য যাচাই ও সম্পাদনা করুন।</p>"
        f'<p><a href="{safe_link}" '
        'target="_blank" rel="noopener noreferrer">'
        f'{safe_source} - মূল সংবাদ</a></p>'
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

    print("DRAFT CREATED")
    print("Post ID:", result.get("id"))
    print("Title:", title)

    return True


def collect_news():

    print("Daily Bangla News - WordPress Publisher")

    for source, feed_url in RSS_FEEDS.items():

        print("\nChecking:", source)

        request = urllib.request.Request(
            feed_url,
            headers={"User-Agent": "DailyBanglaNews/1.0"}
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")

        print("News Found:", len(items))

        for item in items[:5]:

            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()

            if title and link:
                print("News:", title)

                if create_draft(title, link, source):
                    print("One draft created. Stopping test.")
                    return

    print("No new draft created.")


if __name__ == "__main__":
    collect_news()
