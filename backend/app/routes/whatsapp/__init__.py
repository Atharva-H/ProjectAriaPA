from fastapi import APIRouter
from app.routes.whatsapp import link_routes, webhook_routes, unlink_routes

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# include subroutes
router.include_router(link_routes.router)
router.include_router(webhook_routes.router)
router.include_router(unlink_routes.router)
