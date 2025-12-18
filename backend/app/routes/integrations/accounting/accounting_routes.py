# app/routes/integrations/accounting/accounting_routes.py

"""
Unified accounting integration routes.
Handles multiple accounting software integrations.
"""

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from app.db import get_db, crud
from app.core.security import decode_jwt

router = APIRouter(prefix="/integrations/accounting", tags=["Accounting Integrations"])
logger = logging.getLogger("ProjectAria.AccountingRoutes")


class AccountingConnectRequest(BaseModel):
    software: str  # "tally", "quickbooks", "xero", etc.
    credentials: Dict[str, Any]  # Software-specific credentials


class AccountingDisconnectRequest(BaseModel):
    software: str




@router.post("/connect")
async def connect_accounting(
    request: AccountingConnectRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Connect to an accounting software."""
    try:
        # Decode JWT token
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user
        user = crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Route to specific accounting software handler
        if request.software == "tally":
            # Import Tally routes dynamically to avoid circular imports
            from .tally_routes import connect_tally
            return await connect_tally(
                type('TallyConnectRequest', (), {
                    'server_url': request.credentials.get('server_url'),
                    'company_name': request.credentials.get('company_name')
                })(),
                authorization,
                db
            )
        elif request.software == "quickbooks":
            # TODO: Implement QuickBooks connection
            return {"success": False, "message": "QuickBooks integration not yet implemented"}
        elif request.software == "xero":
            # TODO: Implement Xero connection
            return {"success": False, "message": "Xero integration not yet implemented"}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported accounting software: {request.software}")
            
    except Exception as e:
        logger.error(f"❌ Failed to connect {request.software} for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/disconnect")
async def disconnect_accounting(
    request: AccountingDisconnectRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Disconnect from an accounting software."""
    try:
        # Decode JWT token
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user
        user = crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Route to specific accounting software handler
        if request.software == "tally":
            # Import Tally routes dynamically to avoid circular imports
            from .tally_routes import disconnect_tally
            return await disconnect_tally(authorization, db)
        elif request.software == "quickbooks":
            # TODO: Implement QuickBooks disconnection
            return {"success": False, "message": "QuickBooks integration not yet implemented"}
        elif request.software == "xero":
            # TODO: Implement Xero disconnection
            return {"success": False, "message": "Xero integration not yet implemented"}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported accounting software: {request.software}")
            
    except Exception as e:
        logger.error(f"❌ Failed to disconnect {request.software} for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/data/{software}")
async def get_accounting_data(
    software: str,
    data_type: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get data from an accounting software."""
    try:
        # Decode JWT token
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user
        user = crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Route to specific accounting software handler
        if software == "tally":
            # Import Tally routes dynamically to avoid circular imports
            from .tally_routes import get_tally_data
            return await get_tally_data(data_type, authorization, db)
        elif software == "quickbooks":
            # TODO: Implement QuickBooks data retrieval
            return {"success": False, "message": "QuickBooks integration not yet implemented"}
        elif software == "xero":
            # TODO: Implement Xero data retrieval
            return {"success": False, "message": "Xero integration not yet implemented"}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported accounting software: {software}")
            
    except Exception as e:
        logger.error(f"❌ Failed to get {data_type} from {software} for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
