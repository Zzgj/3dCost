from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.responses import APIError, api_error_handler
from app.routers import settings as settings_router
from app.routers import backups, health, machines, materials, parts, print_items, products, purchases, quotes, stats, suppliers


@asynccontextmanager
async def lifespan(app: FastAPI):
    import app.models  # noqa: F401  确保模型注册
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="3dcost", version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(APIError, api_error_handler)

app.include_router(health.router)
app.include_router(materials.router)
app.include_router(parts.router)
app.include_router(suppliers.router)
app.include_router(machines.router)
app.include_router(purchases.router)
app.include_router(print_items.router)
app.include_router(products.router)
app.include_router(quotes.router)
app.include_router(stats.router)
app.include_router(backups.router)
app.include_router(settings_router.router)
