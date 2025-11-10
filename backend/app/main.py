import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, File, Handler, Endpoint, CFGNode, CFGEdge

DATABASE_URL = os.environ.get("DATABASE_URL",
                              "postgresql+psycopg2://postgres:password@postgres:5432/postgres")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Arch-Visualizer MVP")

@app.on_event("startup")
def startup():
    # create tables
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/scan")
def scan(db = Depends(get_db)):
    # run_scan file business logic will be here ...
    node1 = Endpoint(id='10', path="/qwesds", method='GET')
    db.add(node1)
    db.flush()
    db.commit()
    #

    return {"status": "ok"}

@app.get("/graph")
def graph(db = Depends(get_db)):
    nodes = []
    edges = []
    # endpoints
    for ep in db.query(Endpoint).all():
        nid = f"ep:{ep.id}"
        nodes.append({"id": nid, "label": f"{ep.method} {ep.path}", "type": "endpoint", "handler": ep.handler_id})
        if ep.handler:
            edges.append({"from": nid, "to": f"h:{ep.handler.id}", "label": "serves"})
    # handlers
    for h in db.query(Handler).all():
        nid = f"h:{h.id}"
        nodes.append({"id": nid, "label": h.name, "type": "handler", "file": h.file.path if h.file else None})
        # handler -> cfg nodes
        for cn in db.query(CFGNode).filter_by(handler_id=h.id).all():
            cnid = f"cn:{cn.id}"
            nodes.append({"id": cnid, "label": cn.label, "type": "cfg", "lineno": cn.lineno})
            edges.append({"from": f"h:{h.id}", "to": cnid, "label": "contains"})
    # cfg edges
    for e in db.query(CFGEdge).all():
        edges.append({"from": f"cn:{e.src_id}", "to": f"cn:{e.dst_id}", "label": e.label})
    return {"nodes": nodes, "edges": edges}
