import re
import urllib.parse
from typing import List, Dict
import httpx
import lxml.html

class KeylessSearchEngine:
    def __init__(self, timeout: float = 6.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.client = httpx.Client(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
            verify=False
        )

    def extract_urls_from_text(self, text: str) -> List[str]:
        """Extract explicit URLs mentioned directly inside the query string."""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        matches = re.findall(url_pattern, text)
        clean = []
        for m in matches:
            if not m.startswith("http"):
                m = "https://" + m
            clean.append(m)
        return clean

    def search_duckduckgo_lite(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Scrape DuckDuckGo Lite using ultra-fast lxml."""
        results = []
        try:
            url = "https://lite.duckduckgo.com/lite/"
            data = {"q": query}
            resp = self.client.post(url, data=data)
            if resp.status_code == 200:
                tree = lxml.html.fromstring(resp.text)
                links = tree.xpath("//a[contains(@class, 'result-link')]")
                for link in links:
                    href = link.get("href", "")
                    if "uddg=" in href:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        href = parsed.get("uddg", [href])[0]

                    title = link.text_content().strip()
                    if href and href.startswith("http"):
                        results.append({
                            "title": title,
                            "url": href,
                            "snippet": ""
                        })
                        if len(results) >= max_results:
                            break
        except Exception:
            pass
        return results

    def search_duckduckgo_html(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Fallback to DuckDuckGo HTML endpoint with lxml."""
        results = []
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            resp = self.client.get(url)
            if resp.status_code == 200:
                tree = lxml.html.fromstring(resp.text)
                link_elems = tree.xpath("//a[contains(@class, 'result__url')]")
                title_elems = tree.xpath("//a[contains(@class, 'result__title')]")
                snippet_elems = tree.xpath("//a[contains(@class, 'result__snippet')]")

                count = min(len(link_elems), max_results)
                for i in range(count):
                    raw_href = link_elems[i].get("href", "")
                    if "uddg=" in raw_href:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                        raw_href = parsed.get("uddg", [raw_href])[0]
                    elif raw_href.startswith("//"):
                        raw_href = "https:" + raw_href

                    title = title_elems[i].text_content().strip() if i < len(title_elems) else ""
                    snippet = snippet_elems[i].text_content().strip() if i < len(snippet_elems) else ""

                    if raw_href and raw_href.startswith("http"):
                        results.append({
                            "title": title,
                            "url": raw_href,
                            "snippet": snippet
                        })
        except Exception:
            pass
        return results

    def search_wikipedia(self, query: str, max_results: int = 2) -> List[Dict[str, str]]:
        """Fast direct search on Wikipedia API (official, zero auth, ultra-reliable)."""
        results = []
        try:
            clean_q = re.sub(r'[^\w\s]', '', query).strip()
            api_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(clean_q)}&limit={max_results}&namespace=0&format=json"
            resp = self.client.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 4:
                    titles, snippets, urls = data[1], data[2], data[3]
                    for t, s, u in zip(titles, snippets, urls):
                        results.append({
                            "title": t,
                            "url": u,
                            "snippet": s
                        })
        except Exception:
            pass
        return results

    def search(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Consolidated search orchestrator."""
        # 1. Check if URL is given directly in query
        explicit_urls = self.extract_urls_from_text(query)
        if explicit_urls:
            return [{"title": "Target URL", "url": u, "snippet": ""} for u in explicit_urls]

        # 2. Try DuckDuckGo Lite first (fastest)
        results = self.search_duckduckgo_lite(query, max_results=max_results)
        if not results:
            # 3. Fallback to DDG HTML
            results = self.search_duckduckgo_html(query, max_results=max_results)

        # 4. If still empty or query looks encyclopedic, add Wikipedia
        if not results or len(results) < 2:
            wiki_res = self.search_wikipedia(query, max_results=2)
            results.extend(wiki_res)

        # Deduplicate by URL
        seen = set()
        deduped = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)
        return deduped[:max_results]
