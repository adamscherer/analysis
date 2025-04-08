from pydantic import BaseModel, Field, field_validator
from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class Stock(BaseModel):
    """Model for stock data from NASDAQ and other exchanges."""
    id: str
    symbol: str
    security_name: str
    exchange: str
    market_category: Optional[str] = None
    test_issue: bool = Field(default=False)
    financial_status: Optional[str] = None
    round_lot_size: int = Field(default=100)
    etf: bool = Field(default=False)
    next_shares: bool = Field(default=False)
    cqs_symbol: Optional[str] = None

    @field_validator('round_lot_size')
    @classmethod
    def validate_round_lot_size(cls, v):
        """Ensure round_lot_size is a positive integer."""
        if v <= 0:
            raise ValueError('round_lot_size must be positive')
        return v

    @classmethod
    def from_other_listed(cls, row: pd.Series) -> 'Stock':
        """Create a Stock instance from otherlisted.txt data."""
        # Convert boolean fields and handle NaN values
        etf = row['etf'] == 'Y' if pd.notna(row['etf']) else False
        test_issue = row['test_issue'] == 'Y' if pd.notna(row['test_issue']) else False
        
        # Handle round_lot_size
        round_lot_size = int(row['round_lot_size']) if pd.notna(row['round_lot_size']) else 100
        
        # Handle required string fields
        symbol = str(row['act_symbol']) if pd.notna(row['act_symbol']) else ""
        security_name = str(row['security_name']) if pd.notna(row['security_name']) else ""
        exchange = str(row['exchange']) if pd.notna(row['exchange']) else ""
        
        # Skip records with missing required fields
        if not symbol or not security_name or not exchange:
            logger.warning(f"Skipping record with missing required fields: {row.to_dict()}")
            return None
        
        # Generate composite ID
        id = f"{symbol}:{exchange}"
        
        # Handle optional string fields
        cqs_symbol = str(row['cqs_symbol']) if pd.notna(row['cqs_symbol']) else None
        
        return cls(
            id=id,
            symbol=symbol,
            security_name=security_name,
            exchange=exchange,
            cqs_symbol=cqs_symbol,
            etf=etf,
            test_issue=test_issue,
            round_lot_size=round_lot_size
        )

    @classmethod
    def from_nasdaq_listed(cls, row: pd.Series) -> 'Stock':
        """Create a Stock instance from nasdaqlisted.txt data."""
        # Convert boolean fields and handle NaN values
        etf = row['etf'] == 'Y' if pd.notna(row['etf']) else False
        test_issue = row['test_issue'] == 'Y' if pd.notna(row['test_issue']) else False
        next_shares = row['nextshares'] == 'Y' if pd.notna(row['nextshares']) else False
        
        # Handle round_lot_size
        round_lot_size = int(row['round_lot_size']) if pd.notna(row['round_lot_size']) else 100
        
        # Handle required string fields
        symbol = str(row['symbol']) if pd.notna(row['symbol']) else ""
        security_name = str(row['security_name']) if pd.notna(row['security_name']) else ""
        
        # Skip records with missing required fields
        if not symbol or not security_name:
            logger.warning(f"Skipping record with missing required fields: {row.to_dict()}")
            return None
        
        # Generate composite ID
        id = f"{symbol}:NASDAQ"
        
        # Handle optional string fields
        market_category = str(row['market_category']) if pd.notna(row['market_category']) else None
        financial_status = str(row['financial_status']) if pd.notna(row['financial_status']) else None
        
        return cls(
            id=id,
            symbol=symbol,
            security_name=security_name,
            exchange='NASDAQ',
            market_category=market_category,
            financial_status=financial_status,
            etf=etf,
            test_issue=test_issue,
            next_shares=next_shares,
            round_lot_size=round_lot_size
        ) 