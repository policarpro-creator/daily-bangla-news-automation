
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Daily Bangla News - Free RSS Collector

RSS_FEEDS = {
    "BBC Bangla": "https://feeds.bbci.co.uk/bengali/rss.xml",
    "Google News Bangladesh": (
        "https://news.google.com/rss/search?"
        "q=Bangladesh&hl=bn&gl=BD&ceid=BD:bn"
    ),
}

def collect_news():
    print("Daily Bangla News - RSS Collector")
    print("Started:", datetime.now(timezone.utc).isoformat())

    for source, feed_url in RSS_FEEDS.items():
        print(f"\n--- {source} ---")

        try:
            request = urllib.request.Request(
                feed_url,
                headers={"User-Agent": "DailyBanglaNews/1.0"}
            )

            with urllib.request.urlopen(request, timeout=20) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)
            items = root.findall(".//item")

            if not items:
                print("No news found.")
                continue

            for item in items[:5]:
                title = item.findtext("title", default="").strip()
                link = item.findtext("link", default="").strip()

                if title and link:
                    print("Title:", title)
                    print("Link:", link)
                    print("-" * 40)

        except Exception as error:
            print("Could not collect news:", error)

if __name__ == "__main__":
    collect_news()
