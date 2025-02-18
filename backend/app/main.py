from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message" : "Nice 2 meet U :)"}
