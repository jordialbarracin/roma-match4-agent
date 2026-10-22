import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from src.pipeline.extractor import InformationExtractor

app = FastAPI(title="ROMA Web Intelligence Daemon", version="1.0.0")
extractor = InformationExtractor()

class QueryRequest(BaseModel):
    query: str
    query_id: Optional[str] = "default"
    url: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    citations: List[str]
    confidence: float

@app.get("/health")
def health():
    return {"status": "ok", "service": "roma-web-agent-daemon"}

@app.post("/query", response_model=QueryResponse)
def handle_query(req: QueryRequest):
    try:
        res = extractor.solve(query=req.query, start_url=req.url)
        return QueryResponse(
            answer=res.get("answer", ""),
            citations=res.get("citations", []),
            confidence=float(res.get("confidence", 0.0))
        )
    except Exception as e:
        # Fail-closed policy: never crash, return clean refusal
        return QueryResponse(
            answer="",
            citations=[],
            confidence=0.0
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
