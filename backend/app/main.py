from typing import Literal  # noqa: D100

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .dep_analyzer import analyze_project
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
        dependencies = analyze_project(
            project_path=req.repo_root,
            include_external=not req.include_tests,
            excluded_dirs=[],
            root_module=req.root_module,
            max_depth=req.max_depth,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))  # noqa: B904
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"internal error: {e}")  # noqa: B904

    return ScanResult(
        dependencies=dependencies,
    )
