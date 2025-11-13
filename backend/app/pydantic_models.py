from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path

class ScanRequest(BaseModel):
    repo_root: str
    root_module: str
    include_tests: Optional[bool] = False
    max_depth: int = 0  # 0 = unlimited
    verbose: Optional[bool] = False

class EndpointModel(BaseModel):
    file: str
    function: Optional[str] = None
    path: Optional[str] = None
    methods: Optional[List[str]] = None
    framework: Optional[str] = None  # e.g. fastapi, flask, unknown

class ScanResult(BaseModel):
    dependencies: Optional[Dict[str, Any]] = {}
