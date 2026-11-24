
import os
import json
import base64
import html
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET


# ---------------------------------
# 1. RSS NEWS SOURCES
# ---------------------------------

RSS_FEEDS = {
    "BBC Bangla": "https://feeds.bbci.co.uk/bengali/rss.xml",
    "Google News Bangladesh": (
        "https://news.google.com/rss/search?"
        "q=Bangladesh&hl=bn&gl=BD&ceid=BD:bn"
    ),
}


# ---------------------------------
# 2. WORDPRESS SETTINGS
# ---------------------------------

WP_URL = os.environ["WP_URL"].rstrip("/")
WP_USERNAME = os.environ["WP_USERNAME"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"].replace(" ", "")


# ---------------------------------
# 3. WORDPRESS API CONNECTION
# ---------------------------------

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
        with urllib.request.urlopen(
            request, timeout=30
        ) as response:

            raw = response.read()

            print(
                "WordPress HTTP Status:",
                response.status
            )

            print(
                "Response Content-Type:",
                response.headers.get("Content-Type")
            )

            print(
                "Response Preview:",
                raw[:200]
            )

            if not raw.strip():
                raise RuntimeError(
                    "WordPress returned an empty response."
                )

            return json.loads(
                raw.decode("utf-8-sig")
            )

    except urllib.error.HTTPError as error:

        print("WordPress HTTP Error:", error.code)

        error_body = error.read(1000).decode(
            "utf-8", errors="replace"
        )

        print("Error Response:", error_body)

        raise

    except json.JSONDecodeError as error:

        print("Invalid JSON response:", error)

        raise


# ---------------------------------
# 4. CHECK DUPLICATE NEWS
# ---------------------------------

def already_exists(title):

    query = urllib.parse.urlencode({
        "search": title,
        "per_page": 100,
    })

    url = (
        f"{WP_URL}/wp-json/wp/v2/posts?"
        f"{query}"
    )

    posts = wp_request(url)

    for post in posts:

        existing_title = (
            post.get("title", {}).get("rendered", "")
        )

        if (
            html.unescape(existing_title).strip().lower()
            == title.strip().lower()
        ):

            print("Already exists:", title)

            return True

    return False


# ---------------------------------
# 5. CREATE WORDPRESS DRAFT
# ---------------------------------

def create_draft(title, link, source):

    print("Checking duplicate:", title)

    if already_exists(title):
        return False

    safe_link = html.escape(link, quote=True)
    safe_source = html.escape(source)

    content = (
        "<p>এই সংবাদটি মূল সংবাদসূত্র থেকে সংগৃহীত।"
        " প্রকাশের আগে তথ্য যাচাই ও সম্পাদনা করুন।</p>"
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

    print("--------------------------------")
    print("SUCCESS: WORDPRESS DRAFT CREATED")
    print("Post ID:", result.get("id"))
    print("Post Status:", result.get("status"))
    print("Post Title:", title)
    print("--------------------------------")

    return True


# ---------------------------------
# 6. COLLECT RSS NEWS
# ---------------------------------

def collect_news():

    print("================================")
    print("DAILY BANGLA NEWS AUTOMATION")
    print("WordPress Draft Test")
    print("================================")

    for source, feed_url in RSS_FEEDS.items():

        print("\nChecking RSS Source:", source)

        try:

            request = urllib.request.Request(
                feed_url,
                headers={
                    "User-Agent": "DailyBanglaNews/1.0"
                },
            )

            with urllib.request.urlopen(
                request, timeout=30
            ) as response:

                xml_data = response.read()

            root = ET.fromstring(xml_data)

            items = root.findall(".//item")

            print("News Found:", len(items))

            for item in items:

                title = item.findtext(
                    "title", default=""
                ).strip()

                link = item.findtext(
                    "link", default=""
                ).strip()

                if not title or not link:
                    continue

                print("\nNews Title:", title)
                print("News Link:", link)

                created = create_draft(
                    title,
                    link,
                    source,
                )

                if created:
                    print(
                        "Test completed with one draft."
                    )
                    return

            print(
                "No new news available from:",
                source
            )

        except Exception as error:

            print("SOURCE ERROR:", source)
            print("ERROR DETAILS:", str(error))

            raise

    print("No new news could be added.")


# ---------------------------------
# 7. START AUTOMATION
# ---------------------------------

if __name__ == "__main__":

    collect_news()
