from fastapi import FastAPI
from mangum import Mangum
from app.api.messages import router as messages_router
from app.api.webhook import router as webhook_router

app = FastAPI(
    title="Legalink WhatsApp Agent API",
    description="API for handling WhatsApp messages for legal assistance",
    version="0.1.0"
)

# Include routers
app.include_router(messages_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")

# Lambda handler
handler = Mangum(app)

@app.get("/")
async def root():
    return {"message": "Welcome to Legalink WhatsApp Agent API"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "legalink-whatsapp-agent"}
