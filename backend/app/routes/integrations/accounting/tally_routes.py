# app/routes/integrations/tally_routes.py

from fastapi import APIRouter, Header, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from app.db import get_db, crud
from app.core.security import decode_jwt
from app.services.accounting.tally_sql_service import TallySQLService

router = APIRouter(prefix="/integrations/tally", tags=["Tally Integration"])
logger = logging.getLogger("ProjectAria.TallyRoutes")
tally_service = TallySQLService()


class TallyConnectRequest(BaseModel):
    database_name: str
    company_name: Optional[str] = None


class TallyVoucherRequest(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None


@router.post("/connect")
async def connect_tally(
    request: TallyConnectRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Connect to Tally server and save connection details."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    user_data = decode_jwt(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = user_data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"🔗 User {email} attempting to connect to Tally database: {request.database_name}")

    # Test connection to Tally database
    connection_result = await tally_service.test_connection(request.database_name)
    if not connection_result.get("success"):
        logger.error(f"❌ Tally connection failed for {email}: {connection_result.get('message')}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to Tally database: {connection_result.get('message')}"
        )

    # Get company info if not provided
    company_name = request.company_name
    if not company_name:
        logger.info(f"🏢 Fetching company info for {email}")
        company_result = await tally_service.get_company_info(request.database_name)
        if company_result.get("success"):
            company_name = company_result.get("company_name", "Unknown")
            logger.info(f"✅ Company name found: {company_name}")
        else:
            company_name = "Unknown"
            logger.warning(f"⚠️ Could not fetch company name for {email}")

    # Save connection details
    crud.update_tally_connection(
        db, user, request.database_name, company_name, True
    )

    logger.info(f"✅ Tally connected for {email}: {request.database_name} (Company: {company_name})")
    return {
        "success": True,
        "message": "Tally connected successfully",
        "database_name": request.database_name,
        "company_name": company_name
    }


@router.post("/disconnect")
async def disconnect_tally(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Disconnect from Tally integration."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    user_data = decode_jwt(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = user_data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.tally_connected:
        raise HTTPException(status_code=400, detail="Tally is not connected")

    # Disconnect Tally
    crud.disconnect_tally(db, user)

    logger.info(f"🔌 Tally disconnected for {email}")
    return {"success": True, "message": "Tally disconnected successfully"}




@router.get("/sales/specific-date")
async def get_specific_date_sales(
    specific_date: str = Query(..., description="Specific date in YYYY-MM-DD format"),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Fetch sales data for a specific date only."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    user_data = decode_jwt(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = user_data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.tally_connected or not user.tally_database_name:
        raise HTTPException(status_code=400, detail="Tally is not connected")

    logger.info(f"📊 User {email} fetching specific date sales from Tally (date: {specific_date})")

    # Fetch specific date sales from Tally
    result = await tally_service.get_specific_date_sales(user.tally_database_name, specific_date)
    if not result.get("success"):
        logger.error(f"❌ Failed to fetch specific date sales for {email}: {result.get('message')}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch specific date sales: {result.get('message')}"
        )

    logger.info(f"✅ Successfully returned specific date sales for {email}")
    return result

@router.get("/sales/custom-date")
async def get_custom_date_sales(
    custom_end_date: str = Query(..., description="Custom end date in YYYY-MM-DD format"),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Fetch custom date sales data."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    user_data = decode_jwt(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = user_data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.tally_connected or not user.tally_database_name:
        raise HTTPException(status_code=400, detail="Tally is not connected")

    logger.info(f"📊 User {email} fetching custom date sales from Tally (end date: {custom_end_date})")

    # Fetch custom date sales from Tally
    result = await tally_service.get_custom_date_sales(user.tally_database_name, custom_end_date)
    if not result.get("success"):
        logger.error(f"❌ Failed to fetch custom date sales for {email}: {result.get('message')}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch custom date sales: {result.get('message')}"
        )

    logger.info(f"✅ Successfully returned custom date sales for {email}")
    return result

@router.get("/sales/yearly-comparison")
async def get_yearly_sales_comparison(
    current_year: Optional[int] = None,
    custom_end_date: Optional[str] = None,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Fetch year-on-year sales comparison data."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    user_data = decode_jwt(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = user_data.get("sub")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.tally_connected or not user.tally_database_name:
        raise HTTPException(status_code=400, detail="Tally is not connected")

    # Default to current year if not provided
    if not current_year:
        from datetime import datetime
        current_year = datetime.now().year

    logger.info(f"📊 User {email} fetching yearly sales comparison from Tally (current year: {current_year})")

    # Fetch yearly sales comparison from Tally
    result = await tally_service.get_yearly_sales_comparison(user.tally_database_name, current_year, custom_end_date)
    if not result.get("success"):
        logger.error(f"❌ Failed to fetch yearly sales comparison for {email}: {result.get('message')}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch yearly sales comparison: {result.get('message')}"
        )

    logger.info(f"✅ Successfully returned yearly sales comparison for {email}")
    return result
