from fastapi import FastAPI

from app.api.routers import auth

app = FastAPI()
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is running!"}


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}
