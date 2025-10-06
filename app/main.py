from app.api.routers import auth, categories, menu, orders, restaurants, tables
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI()
app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(categories.router)
app.include_router(menu.router)
app.include_router(tables.router)
app.include_router(orders.router)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is running!"}
