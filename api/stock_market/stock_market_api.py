from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from core.stock_market.market_engine import MarketEngine
from logger import stock_logger as logger
router = APIRouter()

@router.post("/update_stock_data")
async def update_stock_data(request: Request):
    """
    Endpoint to update stock market data in the vector database.
    This endpoint processes the request to fetch and update stock market data
    """
    try:
        market_engine = MarketEngine()
        try:
            market_engine.fetch_and_update_market_data()
        except ValueError as ve:
            logger.error(f"ValueError: {str(ve)}")
            raise HTTPException(status_code=400, detail=str(ve))

        return JSONResponse(
            status_code=200,
            content={"status": "success", "code": 200, "message": "Successfully updated stock market data"}
        )    

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating stock data: {str(e)}")