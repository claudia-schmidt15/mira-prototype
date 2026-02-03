from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from whispers import router as whispers_router
from segments import router as segments_router
from routing import router as routing_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Register routers
# -------------------------
app.include_router(whispers_router, prefix="/whisper", tags=["whisper"])
app.include_router(segments_router, prefix="/v1/segments", tags=["segments"])
app.include_router(routing_router, prefix="/route", tags=["routing"])

