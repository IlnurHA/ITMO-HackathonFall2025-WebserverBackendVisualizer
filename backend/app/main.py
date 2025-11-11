import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, File, Handler, Endpoint, CFGNode, CFGEdge
from .pydantic_models import ScanRequest, ScanResult
from .dep_analyzer import analyze_project

#DATABASE_URL = os.environ.get("DATABASE_URL",
#                              "postgresql+psycopg2://postgres:password@postgres:5432/postgres")

#engine = create_engine(DATABASE_URL)
#SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Arch-Visualizer MVP")

@app.on_event("startup")
def startup():
    # create tables
    #Base.metadata.create_all(bind=engine)
    pass

@app.post("/scan", response_model=ScanResult)
def scan(req: ScanRequest):
    try:
        dependencies = analyze_project(
            project_path=req.repo_root,
            include_external=not req.include_tests,
            excluded_dirs=[],
            root_module=req.root_module,
            max_depth=req.max_depth
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"internal error: {e}")

    return ScanResult(
        dependencies=dependencies,
    )

@app.get("/graph")
def graph():
    # nodes = []
    # edges = []
    # # endpoints
    # for ep in db.query(Endpoint).all():
    #     nid = f"ep:{ep.id}"
    #     nodes.append({"id": nid, "label": f"{ep.method} {ep.path}", "type": "endpoint", "handler": ep.handler_id})
    #     if ep.handler:
    #         edges.append({"from": nid, "to": f"h:{ep.handler.id}", "label": "serves"})
    # # handlers
    # for h in db.query(Handler).all():
    #     nid = f"h:{h.id}"
    #     nodes.append({"id": nid, "label": h.name, "type": "handler", "file": h.file.path if h.file else None})
    #     # handler -> cfg nodes
    #     for cn in db.query(CFGNode).filter_by(handler_id=h.id).all():
    #         cnid = f"cn:{cn.id}"
    #         nodes.append({"id": cnid, "label": cn.label, "type": "cfg", "lineno": cn.lineno})
    #         edges.append({"from": f"h:{h.id}", "to": cnid, "label": "contains"})
    # # cfg edges
    # for e in db.query(CFGEdge).all():
    #     edges.append({"from": f"cn:{e.src_id}", "to": f"cn:{e.dst_id}", "label": e.label})
    return {"nodes": [], "edges": []}
