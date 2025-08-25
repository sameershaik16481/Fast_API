from app.api.routers import auth, restaurants
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI()
app.include_router(auth.router)
app.include_router(restaurants.router)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is running!"}
