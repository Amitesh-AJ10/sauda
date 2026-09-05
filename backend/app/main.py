from fastapi import FastAPI

app = FastAPI(title="Sauda")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
