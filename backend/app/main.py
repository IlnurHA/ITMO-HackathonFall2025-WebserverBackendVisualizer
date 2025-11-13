from typing import Literal  # noqa: D100

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .dep_analyzer import get_json_dict
from .pydantic_models import ScanRequest, ScanResult

app = FastAPI(title="Arch-Visualizer MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def healthcheck() -> dict[Literal["status"], str]:  # noqa: D103
    return {"status": "ok"}


@app.post("/scan", response_model=ScanResult)
def scan(req: ScanRequest) -> ScanRequest:  # noqa: D103
    try:
        dependencies = get_json_dict(
            project_path=req.repo_root,
            included_external=not req.include_tests,
            max_depth=req.max_depth,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))  # noqa: B904
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"internal error: {e}")  # noqa: B904

    return ScanResult(
        dependencies=dependencies,
    )
