from fastapi import APIRouter
from datetime import datetime
from typing import List

from schemas import WhisperCreate, WhisperOut

router = APIRouter(prefix="/whisper")

# In-memory store (prototype only)
whispers: List[WhisperOut] = []

@router.post("/", response_model=WhisperOut)
def add_whisper(data: WhisperCreate):
    whisper = WhisperOut(
        value=data.value,
        timestamp=datetime.utcnow()
    )
    whispers.append(whisper)
    return whisper

@router.get("/latest", response_model=WhisperOut | None)
def get_latest_whisper():
    return whispers[-1] if whispers else None

@router.get("/recent", response_model=list[WhisperOut])
def get_recent_whispers(limit: int = 3):
    return whispers[-limit:]
