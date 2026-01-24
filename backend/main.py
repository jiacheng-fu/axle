from fastapi import FastAPI
from routes.compare import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Used Car Intelligence API")

app.include_router(router)

@app.get("/")
def health():
    return {"status": "ok"}
