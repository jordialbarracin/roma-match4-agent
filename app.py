#!/usr/bin/env python3
import sys
import os
import json
import argparse
import tempfile
import httpx

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def parse_args():
    parser = argparse.ArgumentParser(description="ROMA Autonomous Web Retrieval Agent - Match 4", add_help=False)
    
    # Query identifier aliases
    parser.add_argument("--query-id", "--query_id", "--id", "--task-id", dest="query_id", type=str, default="query_01")
    
    # Query text aliases
    parser.add_argument("--query", "--question", "--q", "--task", "--prompt", dest="query", type=str, default="")
    
    # Starting URL aliases
    parser.add_argument("--url", "--start-url", "--start_url", "--website", "--site", dest="url", type=str, default=None)
    
    # Output directory
    default_out = os.environ.get("AGENT_OUTPUT", "/app/output")
    parser.add_argument("--output-dir", "--output", dest="output_dir", type=str, default=default_out)
    
    # Compatibility hooks (no-op or warmup)
    parser.add_argument("--index", dest="index_path", type=str, default=None)
    parser.add_argument("--corpus", dest="corpus_path", type=str, default=None)
    parser.add_argument("--warmup", action="store_true")
    parser.add_argument("--serve", action="store_true")

    # Positional fallback
    parser.add_argument("positional_args", nargs="*", default=[])
    
    return parser.parse_known_args()[0]

def query_daemon(query: str, query_id: str, url: str = None) -> dict:
    """Attempt fast RPC to resident daemon."""
    try:
        resp = httpx.post(
            "http://127.0.0.1:8000/query",
            json={"query": query, "query_id": query_id, "url": url},
            timeout=22.0
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def fallback_direct_solve(query: str, url: str = None) -> dict:
    """In-process extraction engine."""
    from src.pipeline.extractor import InformationExtractor
    extractor = InformationExtractor()
    return extractor.solve(query=query, start_url=url)

def write_atomic_json(target_path: str, data: dict):
    """Write atomically to prevent partially written files on container kill."""
    dir_name = os.path.dirname(target_path)
    os.makedirs(dir_name, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix="tmp_roma_", suffix=".json")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, target_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def main():
    args = parse_args()

    # Handle serve mode hook
    if args.serve:
        import uvicorn
        from src.daemon.server import app
        uvicorn.run(app, host="127.0.0.1", port=8000)
        return

    # Handle warmup hook
    if args.warmup or args.index_path:
        print("[ROMA] Warmup completed successfully.")
        return

    # Resolve query string
    query = args.query
    if not query and args.positional_args:
        query = " ".join(args.positional_args)
    if not query:
        query = os.environ.get("QUERY", os.environ.get("AGENT_QUERY", ""))

    query_id = args.query_id or os.environ.get("QUERY_ID", "query_01")
    url = args.url or os.environ.get("URL", os.environ.get("START_URL", None))

    out_filename = f"{query_id}_output.json"
    out_path = os.path.join(args.output_dir, out_filename)

    # Hard gate safety: Write initial empty valid JSON immediately
    fallback_empty = {
        "answer": "",
        "citations": [],
        "sources": [],
        "source_url": "",
        "confidence": 0.0
    }
    write_atomic_json(out_path, fallback_empty)

    if not query:
        print(json.dumps(fallback_empty))
        return

    # 1. Fast query daemon in VRAM
    result = query_daemon(query, query_id, url)

    # 2. In-process fallback
    if result is None:
        result = fallback_direct_solve(query, url)

    # Normalization & schema guarantee
    citations = list(result.get("citations", []))
    sources = list(result.get("sources", citations))
    primary_src = result.get("source_url") or (citations[0] if citations else "")

    final_payload = {
        "answer": str(result.get("answer", "")),
        "citations": citations,
        "sources": sources,
        "source_url": primary_src,
        "confidence": float(result.get("confidence", 0.0))
    }

    # Write final verified payload atomically
    write_atomic_json(out_path, final_payload)
    print(json.dumps(final_payload))

if __name__ == "__main__":
    main()
