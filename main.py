from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import hash_password, verify_password, create_access_token
from routers import countries, links, mappoints, maps

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(maps.router)
app.include_router(countries.router)
app.include_router(mappoints.router)
app.include_router(links.router)

class RegisterIn(BaseModel):
    name:         str
    display_name: str
    password:     str

class LoginIn(BaseModel):
    name:    str
    password: str

@app.post("/api/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.name == body.name).first():
        raise HTTPException(status_code=400, detail="すでに登録済みのユーザー名です")
    user = User(
        name=body.name,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        role="editor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "display_name": user.display_name, "role": user.role}

@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == body.name).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="ユーザー名またはパスワードが間違っています")
    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer",
            "display_name": user.display_name, "role": user.role}