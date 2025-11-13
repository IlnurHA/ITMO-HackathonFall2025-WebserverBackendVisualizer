from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .dep_analyzer import get_json_dict
from .pydantic_models import ScanRequest, ScanResult

app = FastAPI(title="Arch-Visualizer MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def healthcheck() -> dict[Literal["status"], str]:
    return {"status": "ok"}

@app.post("/scan", response_model=ScanResult)
def scan(req: ScanRequest) -> ScanResult:
    try:
        dependencies = get_json_dict(
            project_path=req.repo_root,
            included_external=not req.include_tests,
            max_depth=req.max_depth,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"internal error: {e}")

    return ScanResult(dependencies=dependencies)

@app.get("/graph")
def test_graph():
    return {"message": "This is a test endpoint - use POST /scan instead"}