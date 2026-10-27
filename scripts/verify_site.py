"""Verify the existing public static publication against the checked-out source."""
import hashlib
import sys
import time
from urllib.error import URLError
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://aithos-vulkan-tensor-parallel.vercel.app"
REPO = "https://github.com/aithosinnovation/aithos-vulkan-tensor-parallel"
FILES = {
    "/": "docs/index.html",
    "/beginner.html": "docs/beginner.html",
    "/style.css": "docs/style.css",
    "/app.js": "docs/app.js",
    "/data.js": "docs/data.js",
    "/data.json": "docs/data.json",
    "/data/samples.csv": "data/samples.csv",
    "/assets/comparison.png": "assets/comparison.png",
}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for key, value in attrs:
                if key == "href" and value and value.startswith(REPO + "/blob/main/"):
                    self.links.add(value)


def fetch(url):
    request = Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "Aithos-publication-verifier"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}: {url}")
        return response.read(), response.url


def verify(site=SITE):
    links = Links()
    for route, path in FILES.items():
        actual, final_url = fetch(site + route)
        if final_url != site + route:
            raise ValueError(f"Unexpected redirect: {route}")
        expected = (ROOT / path).read_bytes()
        if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest():
            raise ValueError(f"Live bytes differ from this commit: {route}")
        if path.endswith(".html"):
            html = actual.decode("utf-8")
            if "github.com/ritmaxer/aithos-vulkan-tensor-parallel" in html:
                raise ValueError("A former-owner repository link remains in the live HTML.")
            links.feed(html)
    expected_links = {REPO + "/blob/main/" + name for name in ("README.md", "METHOD.md", "VERIFY.md", "references.md")}
    if links.links != expected_links:
        raise ValueError("Canonical report link set differs from the approved publication.")
    for url in sorted(links.links):
        _, final_url = fetch(url)
        if final_url != url:
            raise ValueError("Canonical report URL unexpectedly redirects.")
    print("PASS: 8 live resources match this commit; 4 canonical report links work.")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise SystemExit("Usage: verify_site.py [public deployment base URL]")
    site = sys.argv[1].rstrip("/") if len(sys.argv) == 2 else SITE
    if not site.startswith("https://aithos-vulkan-tensor-parallel") or not site.endswith(".vercel.app"):
        raise SystemExit("Expected a benchmark Vercel deployment URL.")
    for attempt in range(3):
        try:
            verify(site)
            break
        except (URLError, ValueError, OSError) as error:
            if attempt == 2:
                raise
            print(f"Publication verification not ready ({type(error).__name__}); retrying shortly.")
            time.sleep(2)
