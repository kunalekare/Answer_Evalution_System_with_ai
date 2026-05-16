from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test():
    return {"status": "ok", "message": "minimal app working"}

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal test app on port 9000...")
    uvicorn.run(app, host="0.0.0.0", port=9000)
