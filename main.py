from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow Chrome extension + Google Maps to talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/score/route")
def score_route():
    return {
        "city": "NYC",
        "score": 72,
        "label": "comfortable",
        "color": "green"
    }

