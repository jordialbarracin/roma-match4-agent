import re
from typing import Dict, Any, List, Optional, Tuple
from src.retrieval.search import KeylessSearchEngine
from src.retrieval.scraper import WebScraper
from src.pipeline.normalizer import clean_exact_value
from src.pipeline.specialized import SpecializedLookups

PATTERNS = {
    "temperature": [
        r'(\b\d{1,3}\s*°?\s*[CFcf]\b)',
        r'(\b\d{1,3}\s*deg(?:rees?)?\s*[CFcf]\b)'
    ],
    "price": [
        r'(\$\s*\d+(?:[.,]\d{2})?)',
        r'(\b\d+(?:[.,]\d{2})?\s*(?:USD|EUR|GBP|€|£)\b)'
    ],
    "date": [
        r'(\b\d{4}-\d{2}-\d{2}\b)',
        r'(\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b)',
        r'(\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b)',
        r'(\b(?:19|20)\d{2}\b)'
    ],
    "version": [
        r'(\bv?\d+\.\d+(?:\.\d+)*(?:-[a-zA-Z0-9.]+)?\b)'
    ],
    "number": [
        r'(\b\d+(?:[.,]\d+)?\b)'
    ]
}

class InformationExtractor:
    def __init__(self, llm_engine=None):
        self.search_engine = KeylessSearchEngine(timeout=6.0)
        self.scraper = WebScraper(timeout=8.0)
        self.specialized = SpecializedLookups(timeout=4.0)
        self.llm_engine = llm_engine

    def classify_target_entity(self, query: str) -> str:
        """Classify expected value type from query intent."""
        q_lower = query.lower()
        if any(w in q_lower for w in ["phone", "telephone", "contact number", "call"]):
            return "phone"
        if any(w in q_lower for w in ["ceo", "chief executive", "who leads", "who is the head"]):
            return "ceo"
        if any(w in q_lower for w in ["temperature", "temp", "thermal", "degrees", "celsius", "fahrenheit"]):
            return "temperature"
        if any(w in q_lower for w in ["price", "cost", "how much", "$", "usd", "euro", "eur"]):
            return "price"
        if any(w in q_lower for w in ["when", "date", "founded", "release", "launch", "year", "born", "end of life", "eol"]):
            return "date"
        if any(w in q_lower for w in ["version", "release tag", "revision"]):
            return "version"
        return "general"

    def extract_core_subject(self, query: str) -> List[str]:
        """Extract key distinctive nouns/tokens from query to ensure page relevance."""
        stopwords = {
            "what", "when", "where", "which", "who", "whom", "how", "much", "many",
            "this", "that", "from", "with", "find", "give", "tell", "current", "latest",
            "version", "package", "release", "date", "phone", "number", "for", "the",
            "and", "are", "can", "you", "does", "reach", "life", "end"
        }
        words = re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', query)
        distinctive = [w for w in words if w.lower() not in stopwords]
        return distinctive

    def rank_passages(self, text: str, query: str, top_k: int = 6) -> List[str]:
        """Rank paragraphs by keyword match density."""
        keywords = set(self.extract_core_subject(query))
        if not keywords:
            return text.splitlines()[:top_k]

        paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 15]
        scored = []
        for p in paragraphs:
            p_words = set(re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', p.lower()))
            overlap = len(keywords & p_words)
            if overlap > 0:
                scored.append((overlap, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:top_k]]

    def extract_from_infobox(self, text: str, query: str) -> Optional[str]:
        """Look for Infobox-style Key: Value lines."""
        q_words = [w.lower() for w in self.extract_core_subject(query)]
        for line in text.splitlines():
            line_clean = line.strip()
            if ":" in line_clean or " | " in line_clean:
                parts = re.split(r'[:|]', line_clean, maxsplit=1)
                if len(parts) == 2:
                    key, val = parts[0].strip().lower(), parts[1].strip()
                    if any(w in key for w in q_words) and val:
                        val = re.split(r'[;\(\[\{]', val)[0].strip()
                        if 1 < len(val) < 60:
                            return clean_exact_value(val)
        return None

    def extract_from_page(self, page_data: Dict[str, Any], query: str, target_type: str) -> Optional[Tuple[str, float]]:
        """Extract exact value candidate from page text or tables with strict confidence."""
        text = page_data.get("text", "")
        top_passages = self.rank_passages(text, query, top_k=6)

        # Handle phone intent
        if target_type == "phone":
            phone = self.specialized.check_phone(text)
            if phone:
                return phone, 0.98

        # Handle CEO intent
        if target_type == "ceo":
            # 1. Check if page title is the person's name
            title = page_data.get("title", "").split(" - ")[0].strip()
            if title and len(title.split()) in [2, 3] and ("ceo" in text.lower() or "chief executive" in text.lower()):
                if any(subj.lower() in text.lower() for subj in self.extract_core_subject(query)):
                    return title, 0.98

            # 2. Check for "Name (chair & CEO)" or "Name (CEO)"
            m_paren = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\([^)]*CEO[^)]*\)', text)
            if m_paren:
                return m_paren.group(1).strip(), 0.96

            # 3. Line scan
            for line in text.splitlines():
                if "ceo" in line.lower() or "chief executive" in line.lower():
                    m = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)[^a-zA-Z0-9]+(?:chair\s*&\s*)?CEO\b', line)
                    if m:
                        return m.group(1).strip(), 0.95
                    m2 = re.search(r'\bCEO[^a-zA-Z0-9]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', line)
                    if m2:
                        return m2.group(1).strip(), 0.95

        # Type-specific pattern match on relevant passages
        if target_type in PATTERNS and top_passages:
            for passage in top_passages:
                for pat in PATTERNS[target_type]:
                    matches = re.findall(pat, passage)
                    if matches:
                        cand = clean_exact_value(matches[0])
                        if cand:
                            return cand, 0.95

        # Check infobox key-value format
        infobox_cand = self.extract_from_infobox(text, query)
        if infobox_cand:
            return infobox_cand, 0.90

        if not top_passages:
            return None

        # General extractor: look for key phrases
        for passage in top_passages:
            m = re.search(r'(?:is|was|founded\s+in|founded|released\s+on|launched|priced\s+at)\s+([A-Za-z0-9\s,.-]{1,40}?)(?:\.|\;|\n|\(|$)', passage, re.IGNORECASE)
            if m:
                cand = clean_exact_value(m.group(1))
                if len(cand) > 1 and len(cand) < 50:
                    return cand, 0.80

        return None

    def solve(self, query: str, start_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Main solver adhering strictly to the AMD AI League Match 4 contract.
        Outputs exact schema:
        {
            "answer": "...",
            "citations": ["..."],
            "sources": ["..."],
            "source_url": "...",
            "confidence": ...
        }
        """
        q_lower = query.lower()

        # 1. Package registries: Check PyPI / npm
        if "pypi" in q_lower:
            pypi_res = self.specialized.check_pypi(query)
            if pypi_res:
                version, pypi_url = pypi_res
                return {
                    "answer": version,
                    "citations": [pypi_url],
                    "sources": [pypi_url],
                    "source_url": pypi_url,
                    "confidence": 0.99
                }
            else:
                # Direct PyPI inquiry failed -> package does not exist -> refuse immediately
                return {"answer": "", "citations": [], "sources": [], "source_url": "", "confidence": 0.0}

        if "npm" in q_lower:
            npm_res = self.specialized.check_npm(query)
            if npm_res:
                version, npm_url = npm_res
                return {
                    "answer": version,
                    "citations": [npm_url],
                    "sources": [npm_url],
                    "source_url": npm_url,
                    "confidence": 0.99
                }
            else:
                return {"answer": "", "citations": [], "sources": [], "source_url": "", "confidence": 0.0}

        target_type = self.classify_target_entity(query)
        core_subjects = self.extract_core_subject(query)

        # 2. Gather candidates
        pages_to_check = []
        if start_url:
            pages_to_check.append(start_url)
        else:
            hits = self.search_engine.search(query, max_results=3)
            for h in hits:
                pages_to_check.append(h["url"])

        # 3. Scrape and extract with strict substring verification
        for url in pages_to_check:
            page_data = self.scraper.scrape(url, max_chars=25000)
            if not page_data or not page_data.get("text"):
                continue

            page_text_lower = page_data["text"].lower()

            # Necessity test: The page must contain at least one of the primary distinctive query subjects
            if core_subjects:
                grounded = any(subj.lower() in page_text_lower for subj in core_subjects)
                if not grounded:
                    # Page is completely ungrounded for this query, ignore it!
                    continue

            extracted = self.extract_from_page(page_data, query, target_type)
            if extracted:
                answer, confidence = extracted
                # Strict verification: Substring containment test
                # Ensure the answer is literally inside the page text
                if answer.lower() in page_text_lower or (page_data.get("tables") and answer.lower() in str(page_data["tables"]).lower()):
                    # Year refinement if explicitly requested
                    if "year" in query.lower() and not "years" in query.lower():
                        m_year = re.search(r'\b(18\d{2}|19\d{2}|20\d{2})\b', answer)
                        if m_year:
                            answer = m_year.group(1)

                    return {
                        "answer": answer,
                        "citations": [url],
                        "sources": [url],
                        "source_url": url,
                        "confidence": round(confidence, 2)
                    }

        # 4. Abstention / Refusal (Hard gate compliance)
        return {
            "answer": "",
            "citations": [],
            "sources": [],
            "source_url": "",
            "confidence": 0.0
        }
