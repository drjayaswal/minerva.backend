from pydantic import BaseModel, EmailStr

class ConnectRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    token: str
    email: str
    id: str