from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from alpaca_alp.market_data import AlpacaMarketData

app = FastAPI(title="Options Trading API")
market_data = AlpacaMarketData()

class StrategyValidation(BaseModel):
    symbol: str
    min_volatility: Optional[float] = None
    price_range: Optional[List[float]] = None
    max_delta: Optional[float] = None
    min_theta: Optional[float] = None
    max_vega: Optional[float] = None

@app.get("/stock/{symbol}")
async def get_stock_data(symbol: str):
    """Get current stock price and market data."""
    result = market_data.get_stock_price(symbol)
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    return result

@app.get("/options/{symbol}")
async def get_option_chain(symbol: str, expiration: Optional[str] = None):
    """Get option chain for a symbol."""
    result = market_data.get_option_chain(symbol, expiration)
    if result and 'error' in result[0]:
        raise HTTPException(status_code=400, detail=result[0]['error'])
    return result

@app.get("/volatility/{symbol}")
async def get_volatility(symbol: str, days: int = 30):
    """Get historical volatility for a symbol."""
    result = market_data.get_historical_volatility(symbol, days)
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    return result

@app.get("/market/{symbol}")
async def get_market_conditions(symbol: str):
    """Get comprehensive market conditions for a symbol."""
    result = market_data.get_market_conditions(symbol)
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    return result

@app.post("/validate-strategy")
async def validate_strategy(strategy: StrategyValidation):
    """Validate if current market conditions meet strategy requirements."""
    result = market_data.validate_strategy_conditions(strategy.dict())
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
