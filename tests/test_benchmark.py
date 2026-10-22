import time
import json
import os
import sys

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline.extractor import InformationExtractor

def run_tests():
    extractor = InformationExtractor()
    test_cases = [
        {
            "name": "PyPI Package Version (Requests)",
            "query": "What is the latest version of the requests package on PyPI?",
            "url": None,
            "expected_answer": "2.34.2",
            "must_refuse": False
        },
        {
            "name": "IRS Tax Help Phone Number (Starting URL)",
            "query": "What is the phone number for individual tax help?",
            "url": "https://www.irs.gov/help/telephone-assistance",
            "expected_answer": "800-829-1040",
            "must_refuse": False
        },
        {
            "name": "NVIDIA Founding Year",
            "query": "In what year was NVIDIA founded?",
            "url": None,
            "expected_answer": "1993",
            "must_refuse": False
        },
        {
            "name": "AMD CEO Lookup",
            "query": "Who is the CEO of AMD?",
            "url": None,
            "expected_answer": "Lisa Su",
            "must_refuse": False
        },
        {
            "name": "Negative Trap: Nonexistent PyPI package",
            "query": "What is the latest version of the PyPI package zzqx-nonexistent-pkg-4821?",
            "url": None,
            "expected_answer": "",
            "must_refuse": True
        },
        {
            "name": "Negative Trap: Fictional Entity Phone",
            "query": "What is the phone number of Zentrovax Quantum Bakery Ltd?",
            "url": None,
            "expected_answer": "",
            "must_refuse": True
        }
    ]

    print("=========================================================")
    print("      ROMA AGENT - AMD AI LEAGUE BENCHMARK SUITE         ")
    print("=========================================================\n")

    passed = 0
    total = len(test_cases)

    for i, tc in enumerate(test_cases, 1):
        print(f"[{i}/{total}] Testing: {tc['name']}")
        print(f"       Query: '{tc['query']}'")
        if tc["url"]:
            print(f"       URL: {tc['url']}")

        t0 = time.time()
        res = extractor.solve(query=tc["query"], start_url=tc["url"])
        elapsed = time.time() - t0

        answer = res.get("answer", "")
        citations = res.get("citations", [])
        confidence = res.get("confidence", 0.0)

        print(f"       -> Answer: '{answer}' | Confidence: {confidence} | Time: {elapsed:.2f}s")
        print(f"       -> Citations: {citations}")

        # Check time limit hard gate (30s max)
        assert elapsed < 30.0, f"Query exceeded 30s limit! ({elapsed:.2f}s)"

        if tc["must_refuse"]:
            if answer == "" and len(citations) == 0:
                print("       [PASS] Correctly abstained with empty citation list.\n")
                passed += 1
            else:
                print("       [FAIL] Failed to refuse ungrounded query!\n")
        else:
            if answer == tc["expected_answer"] and len(citations) > 0:
                print("       [PASS] Exact answer match with verified citation.\n")
                passed += 1
            else:
                print(f"       [CHECK] Expected '{tc['expected_answer']}', got '{answer}'.\n")

    print("=========================================================")
    print(f"BENCHMARK RESULTS: {passed}/{total} PASSED")
    print("=========================================================")

if __name__ == "__main__":
    run_tests()
