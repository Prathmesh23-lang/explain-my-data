from fastapi import FastAPI
from database import SessionLocal
from models import User

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Backend is running"}


@app.get("/test-db")
def test_db():
    try:
        db = SessionLocal()

        new_user = User(
            email="test@example.com",
            password_hash="test123"
        )

        db.add(new_user)
        db.commit()

        return {"message": "User inserted"}

    except Exception as e:
        return {"error": str(e)}