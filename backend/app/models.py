from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, JSON, create_engine
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path

Base = declarative_base()

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String)
    meta = Column(JSON)

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True, nullable=False)

class Handler(Base):
    __tablename__ = "handlers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    lineno = Column(Integer)
    meta = Column(JSON)
    file = relationship("File")

class Endpoint(Base):
    __tablename__ = "endpoints"
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)
    method = Column(String, nullable=False)
    handler_id = Column(Integer, ForeignKey("handlers.id"), nullable=True)
    handler = relationship("Handler")

class CFGNode(Base):
    __tablename__ = "cfg_nodes"
    id = Column(Integer, primary_key=True)
    handler_id = Column(Integer, ForeignKey("handlers.id"))
    label = Column(String)
    lineno = Column(Integer)
    meta = Column(JSON)
    handler = relationship("Handler")

class CFGEdge(Base):
    __tablename__ = "cfg_edges"
    id = Column(Integer, primary_key=True)
    src_id = Column(Integer, ForeignKey("cfg_nodes.id"))
    dst_id = Column(Integer, ForeignKey("cfg_nodes.id"))
    label = Column(String)
