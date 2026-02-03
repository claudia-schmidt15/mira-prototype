from pydantic import BaseModel
from datetime import datetime
from typing import List

# -------------------------
# Whisper schemas
# -------------------------
class WhisperCreate(BaseModel):
    value: str

class WhisperOut(BaseModel):
    value: str
    timestamp: datetime

# -------------------------
# Screen-space route schemas
# -------------------------
class ScreenPoint(BaseModel):
    x: float
    y: float

class Viewport(BaseModel):
    width: int
    height: int

class RouteScreenRequest(BaseModel):
    points: List[ScreenPoint]
    viewport: Viewport
