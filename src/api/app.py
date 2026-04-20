from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.config.config import settings

app = FastAPI(
    title="Eleina Agent API",
    description="全能智能体动漫角色Agent API接口",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "欢迎使用 Eleina Agent API", "version": "1.0.0"}


def run_api_server(host: str = None, port: int = None):
    import uvicorn
    host = host or settings.api_host
    port = port or settings.api_port
    uvicorn.run(app, host=host, port=port)