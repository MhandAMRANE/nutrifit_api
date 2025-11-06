from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from controllers.user_controller import signup_user 
from controllers.user_controller import login_user
from controllers.user_controller import verify_code
from database import Base, engine


# Création de la base si besoin
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NutriFit API")

class SignupModel(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str

class LoginModel(BaseModel):
    email: EmailStr
    mot_de_passe: str

class VerifyCodeModel(BaseModel):
    email: EmailStr
    code: str


@app.get("/")
def home():
    return {"message": "Bienvenue sur l'API NutriFit "}

@app.post("/signup")
def signup(data: SignupModel):
    return signup_user(data.nom, data.prenom, data.email, data.mot_de_passe)

@app.post("/verify_code")
def verify(data: VerifyCodeModel):
    return verify_code(data.email, data.code)
@app.post("/login")
def login(data: LoginModel):
    return login_user(data.email, data.mot_de_passe)
