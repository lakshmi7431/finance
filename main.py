from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import auth, dashboard, records
from app.database import Base, engine
from app import users

# Base.metadata.drop_all(engine)
# passwor
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Finance Dashboard API",
    description="Backend for a finance dashboard with role-based access control",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(records.router, prefix="/api/records", tags=["Financial Records"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
def root():
    return {"message": "Finance Dashboard API is running"}