import re
from typing import Optional, Dict, Any
import httpx
import lxml.html

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

class WebScraper:
    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout
        self.client = httpx.Client(
            headers={
                "User-Agent": USER_AGENTS[0],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
            timeout=self.timeout,
            verify=False
        )

    def fetch(self, url: str) -> Optional[str]:
        """Fetch raw HTML from a URL with safety checks."""
        try:
            resp = self.client.get(url)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        return None

    def clean_html(self, raw_html: str, max_chars: int = 15000) -> Dict[str, Any]:
        """Parse and extract clean text and tables from HTML with lxml."""
        if not raw_html:
            return {"title": "", "text": "", "tables": []}

        try:
            tree = lxml.html.fromstring(raw_html)
        except Exception:
            return {"title": "", "text": "", "tables": []}

        # Extract title
        title = ""
        title_nodes = tree.xpath("//title")
        if title_nodes and title_nodes[0].text:
            title = title_nodes[0].text.strip()

        # Remove noise elements
        for bad in tree.xpath("//script | //style | //nav | //footer | //header | //noscript | //svg | //form | //aside"):
            bad.drop_tree()

        # Extract structured data: tables
        tables = []
        for table in tree.xpath("//table"):
            rows = []
            for tr in table.xpath(".//tr"):
                cells = [re.sub(r"\s+", " ", c.text_content().strip()) for c in tr.xpath(".//th | .//td")]
                if cells and any(cells):
                    rows.append(" | ".join(cells))
            if rows:
                tables.append("\n".join(rows))

        # Extract main body text
        text = tree.text_content()
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        clean_lines = [line for line in lines if len(line) > 2]
        clean_text = "\n".join(clean_lines)

        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars]

        return {
            "title": title,
            "text": clean_text,
            "tables": tables,
        }

    def scrape(self, url: str, max_chars: int = 15000) -> Dict[str, Any]:
        """Fetch and clean page content in one call."""
        raw_html = self.fetch(url)
        data = self.clean_html(raw_html, max_chars=max_chars)
        data["url"] = url
        return data
