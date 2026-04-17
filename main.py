from fastapi import FastAPI
from schemas import ItemResponse

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/items", response_model=list[ItemResponse])
def list_items():
    return []
