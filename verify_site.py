#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PAGES = [ROOT / name for name in ("index.html", "privacy.html", "support.html")]
FORBIDDEN = {
    "List-KR": "removed Korean filter source",
    "SafariConverterLib": "removed third-party converter/runtime",
    "모든 앱의 광고": "unsupported universal DNS claim",
    "어떤 서버로도 보내지 않습니다": "claim ignores selected DNS/GitHub providers",
    "어떤 iOS 광고 차단 앱도": "unsupported market-wide claim",
}
REQUIRED_PRIVACY = (
    "GitHub",
    "DNS 제공업체",
    "애드제로 개발자는 해당 제공업체의 운영 로그에 접근하지 않습니다",
    "YousList",
    "CC BY 4.0",
    "CC BY-SA 3.0+",
    "FILTER_LICENSES.md",
)

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.title_depth = 0
        self.title = ""
        self.viewport = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "title":
            self.title_depth += 1
        if tag == "meta" and attrs.get("name") == "viewport":
            self.viewport = bool(attrs.get("content"))

    def handle_endtag(self, tag):
        if tag == "title":
            self.title_depth = max(0, self.title_depth - 1)

    def handle_data(self, data):
        if self.title_depth:
            self.title += data


def main():
    errors = []
    combined = "\n".join(page.read_text(encoding="utf-8") for page in PAGES)
    for needle, reason in FORBIDDEN.items():
        if needle in combined:
            errors.append(f"forbidden text {needle!r}: {reason}")

    for page in PAGES:
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        if not parser.title.strip():
            errors.append(f"{page.name}: missing title")
        if not parser.viewport:
            errors.append(f"{page.name}: missing viewport meta")
        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme or href.startswith("#"):
                continue
            target = ROOT / parsed.path
            if not target.exists():
                errors.append(f"{page.name}: broken local link {href}")

    privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
    for needle in REQUIRED_PRIVACY:
        if needle not in privacy:
            errors.append(f"privacy.html: missing disclosure {needle!r}")

    if errors:
        print("SITE VERIFICATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SITE VERIFICATION PASSED: 3 pages, internal links, claims, privacy disclosures")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
