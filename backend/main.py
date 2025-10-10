from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database, models
from auth import router as auth_router



models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
from whatsapp_routes import router as whatsapp_router
app.include_router(whatsapp_router)


@app.get("/")
def root():
    return {"message": "Backend running"}
