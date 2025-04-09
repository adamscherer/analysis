from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Dict, List, Optional, ClassVar, Any
from datetime import datetime
import pandas as pd
import logging
import json
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

class Stock(BaseModel):
    """Model for stock data from SEC API."""
    cik: str = Field(max_length=10, min_length=10)
    symbol: str
    security_name: str
    entity_type: Optional[str] = None
    sic: Optional[str] = None
    sic_description: Optional[str] = None
    owner_org: Optional[str] = None
    insider_transaction_for_owner_exists: Optional[int] = None
    insider_transaction_for_issuer_exists: Optional[int] = None
    tickers: Optional[List[str]] = None
    exchanges: Optional[List[str]] = None
    ein: Optional[str] = None
    lei: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    investor_website: Optional[str] = None
    category: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    state_of_incorporation_description: Optional[str] = None
    addresses: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    flags: Optional[str] = None
    former_names: Optional[List[Dict[str, Any]]] = None
    basic_shares: Optional[float] = None
    diluted_shares: Optional[float] = None
    dilution_percentage: Optional[float] = None

    # Configure model serialization
    model_config = ConfigDict(
        json_encoders={
            # Convert datetime to ISO format string for JSON serialization
            datetime: lambda dt: dt.isoformat()
        }
    )

    # Class-level configuration
    model_config: ClassVar[Dict] = {
        "json_schema_extra": {
            "examples": [
                {
                    "cik_str": "320193",
                    "symbol": "AAPL",
                    "security_name": "Apple Inc."
                }
            ]
        }
    }

    @classmethod
    def from_sec_json(cls, data: Dict[str, Any]) -> List['Stock']:
        """
        Create Stock instances from SEC API JSON response.
        
        Args:
            data: The JSON response from SEC API
            
        Returns:
            List of Stock objects
        """
        stocks = []

        # Original parsing logic for ticker list format
        for _, company in data.items():
            try:
                # Extract fields
                cik = str(company.get('cik_str', 0)).zfill(10)
                ticker = company.get('ticker', '')
                title = company.get('title', '')
                
                if not ticker or not title:
                    logger.debug(f"Skipping company with missing data: {company}")
                    continue
                
                # Create Stock instance directly
                stock = cls(
                    cik=cik,
                    symbol=ticker,
                    security_name=title
                )
                
                stocks.append(stock)
            except Exception as e:
                logger.error(f"Error creating Stock from company data {company}: {str(e)}")
                continue
        
        logger.info(f"Created {len(stocks)} Stock objects from SEC data")
        return stocks

    @classmethod
    def update_from_submission(cls, stock: 'Stock', submission_data: Dict[str, Any]) -> 'Stock':
        """
        Update an existing Stock object with data from the submissions endpoint.
        
        Args:
            stock: Existing Stock object with basic information
            submission_data: JSON data from the submissions endpoint
            
        Returns:
            Updated Stock object
        """
        try:
            if not submission_data or not isinstance(submission_data, dict):
                logger.warning("Invalid submission data provided")
                return stock

            # Create a new Stock object with original data plus enhanced data
            return cls(
                # Maintain original core fields
                cik=stock.cik,
                symbol=stock.symbol,
                security_name=stock.security_name,
                
                # Add enhanced fields from submission data
                entity_type=submission_data.get('entityType'),
                sic=submission_data.get('sic'),
                sic_description=submission_data.get('sicDescription'),
                owner_org=submission_data.get('ownerOrg'),
                insider_transaction_for_owner_exists=submission_data.get('insiderTransactionForOwnerExists'),
                insider_transaction_for_issuer_exists=submission_data.get('insiderTransactionForIssuerExists'),
                tickers=submission_data.get('tickers'),
                exchanges=submission_data.get('exchanges'),
                ein=submission_data.get('ein'),
                lei=submission_data.get('lei'),
                description=submission_data.get('description'),
                website=submission_data.get('website'),
                investor_website=submission_data.get('investorWebsite'),
                category=submission_data.get('category'),
                fiscal_year_end=submission_data.get('fiscalYearEnd'),
                state_of_incorporation=submission_data.get('stateOfIncorporation'),
                state_of_incorporation_description=submission_data.get('stateOfIncorporationDescription'),
                addresses=submission_data.get('addresses'),
                phone=submission_data.get('phone'),
                flags=submission_data.get('flags'),
                former_names=submission_data.get('formerNames'),
                basic_shares=submission_data.get('basicShares'),
                diluted_shares=submission_data.get('dilutedShares'),
                dilution_percentage=submission_data.get('dilutionPercentage')
            )

        except Exception as e:
            logger.error(f"Error updating stock from submission data: {str(e)}")
            return stock 