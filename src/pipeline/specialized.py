import re
from typing import Optional, Tuple
import httpx

STOP_WORDS = {"the", "a", "an", "latest", "version", "package", "on", "in", "pypi", "npm", "for", "of"}

class SpecializedLookups:
    def __init__(self, timeout: float = 4.0):
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            verify=False,
            headers={"User-Agent": "ROMA-Agent/1.0 (AMD-AI-League)"}
        )

    def extract_package_name(self, query: str) -> Optional[str]:
        """Extract the exact candidate package name from text."""
        # Pattern 1: "<pkg> package"
        m1 = re.search(r'\b([a-zA-Z0-9_\-\.]+)\s+package\b', query, re.IGNORECASE)
        if m1 and m1.group(1).lower() not in STOP_WORDS:
            return m1.group(1)

        # Pattern 2: "package <pkg>" or "package of <pkg>" or "package named <pkg>"
        m2 = re.search(r'\bpackage\s+(?:named\s+|called\s+|for\s+|of\s+(?:the\s+)?)?([a-zA-Z0-9_\-\.]+)\b', query, re.IGNORECASE)
        if m2 and m2.group(1).lower() not in STOP_WORDS:
            return m2.group(1)

        # Pattern 3: words before "on pypi" or "on npm"
        m3 = re.search(r'\b([a-zA-Z0-9_\-\.]+)\s+on\s+(?:pypi|npm)\b', query, re.IGNORECASE)
        if m3 and m3.group(1).lower() not in STOP_WORDS:
            return m3.group(1)

        return None

    def check_pypi(self, query: str) -> Optional[Tuple[str, str]]:
        """Direct, keyless PyPI JSON API check for package version requests."""
        q_lower = query.lower()
        if "pypi" in q_lower or ("package" in q_lower and "version" in q_lower):
            pkg = self.extract_package_name(query)
            if pkg:
                try:
                    resp = self.client.get(f"https://pypi.org/pypi/{pkg}/json")
                    if resp.status_code == 200:
                        data = resp.json()
                        version = data.get("info", {}).get("version")
                        if version:
                            return version, f"https://pypi.org/project/{pkg}/"
                except Exception:
                    pass
        return None

    def check_npm(self, query: str) -> Optional[Tuple[str, str]]:
        """Direct, keyless npm registry check for package version requests."""
        q_lower = query.lower()
        if "npm" in q_lower:
            pkg = self.extract_package_name(query)
            if pkg:
                try:
                    resp = self.client.get(f"https://registry.npmjs.org/{pkg}/latest")
                    if resp.status_code == 200:
                        data = resp.json()
                        version = data.get("version")
                        if version:
                            return version, f"https://www.npmjs.com/package/{pkg}"
                except Exception:
                    pass
        return None

    def check_phone(self, text: str) -> Optional[str]:
        """Extract standardized phone numbers (e.g. 800-829-1040, 800-221-1212)."""
        pattern = r'(\b(?:1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b)'
        matches = re.findall(pattern, text)
        if matches:
            phone = matches[0].strip()
            digits = re.sub(r'\D', '', phone)
            if len(digits) == 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits.startswith("1"):
                return f"{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
            return phone
        return None
