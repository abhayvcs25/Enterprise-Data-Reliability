from fastapi import FastAPI

app=FastAPI()

@app.get("/health")
def health():
    return {"status":"The Back-End is running"}