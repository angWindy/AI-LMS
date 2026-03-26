from fastapi import FastAPI

app = FastAPI(title="LMS API")

@app.get("/")
def root():
    return {"message": "LMS Backend Running"}