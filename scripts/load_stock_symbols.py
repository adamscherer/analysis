import os
import requests
import logging
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
from supabase import create_client
from dotenv import load_dotenv
from src.models import Stock
import time
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# SEC requires a proper user-agent with contact information
# See: https://www.sec.gov/os/accessing-edgar-data
HEADERS = {
    'User-Agent': 'Stock Analysis Tool adam@alphacollider.com',
    'Accept-Encoding': 'gzip, deflate'
}

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL_TEMPLATE = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_FACTS_URL_TEMPLATE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# Rate limiting parameters
# SEC typically allows 10 requests per second per IP address
MAX_REQUESTS_PER_SECOND = 8  # Setting slightly below limit for safety
REQUEST_WINDOW = 10  # Time window in seconds to track requests
request_timestamps = []

def throttle_requests():
    """
    Throttle requests to SEC API to avoid hitting rate limits.
    Uses a sliding window approach to track requests over time.
    """
    global request_timestamps
    current_time = time.time()
    
    # Remove timestamps older than the window
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < REQUEST_WINDOW]
    
    # Check if we're at the rate limit
    if len(request_timestamps) >= MAX_REQUESTS_PER_SECOND * REQUEST_WINDOW:
        # Calculate time to wait - either wait until the oldest timestamp drops off
        # or use a minimum delay
        sleep_time = max(REQUEST_WINDOW - (current_time - request_timestamps[0]), 1)
        logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    # Add jitter to avoid synchronized requests
    jitter = random.uniform(0.1, 0.5)
    time.sleep(jitter)
    
    # Record this request
    request_timestamps.append(time.time())

def fetch_sec_tickers() -> List[Stock]:
    """Fetch basic company data from SEC tickers API and transform into Stock objects."""
    try:
        logger.info(f"Fetching basic company data from SEC: {SEC_TICKERS_URL}")
        
        response = requests.get(SEC_TICKERS_URL, headers=HEADERS)
        response.raise_for_status()
        
        # Parse the JSON data
        sec_data = response.json()
        logger.info(f"Retrieved basic data for {len(sec_data)} companies")
        
        # Use the Pydantic model's class method to create Stock objects
        return Stock.from_sec_json(sec_data)
    except Exception as e:
        logger.error(f"Error fetching SEC ticker data: {str(e)}")
        raise

def fetch_sec_submission_data(stock: Stock) -> Dict[str, Any]:
    """Fetch detailed submission data for a specific CIK."""
    try:
        # Format CIK for URL (ensure it's 10 digits with leading zeros)
        cik = stock.cik

        url = SEC_SUBMISSIONS_URL_TEMPLATE.format(cik=cik)

        logger.info(f"Fetching submission data for {stock.symbol} (CIK: {stock.cik}) from {url}")

        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.warning(f"Rate limit hit for CIK {stock.cik}. Retrying after delay...")
            # On 429, sleep for a longer time and retry once
            time.sleep(random.uniform(5, 10))  # Longer sleep on rate limit
            
            try:
                # Apply throttling again
                throttle_requests()
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                return response.json()
            except Exception as retry_e:
                logger.error(f"Retry failed for CIK {stock.cik}: {str(retry_e)}")
                return None
        else:
            logger.error(f"HTTP error fetching submission data for CIK {stock.cik}: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error fetching submission data for CIK {stock.cik}: {str(e)}")
        return None

def fetch_sec_company_facts(stock: Stock) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Fetch company facts data for a specific CIK to get share count information.
    
    Returns:
        A tuple of (basic_shares, diluted_shares, dilution_percentage)
    """
    try:
        # Format CIK for URL
        cik = stock.cik
        
        url = SEC_COMPANY_FACTS_URL_TEMPLATE.format(cik=cik)
        logger.info(f"Fetching company facts for {stock.symbol} (CIK: {stock.cik}) from {url}")
        
        throttle_requests()
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if the required data is available
        if 'facts' not in data or 'us-gaap' not in data['facts']:
            logger.warning(f"No GAAP data available for {stock.symbol} (CIK: {stock.cik})")
            return None, None, None
        
        gaap = data['facts']['us-gaap']
        
        # Extract basic shares data if available
        basic_shares = None
        if 'WeightedAverageNumberOfSharesOutstandingBasic' in gaap and 'units' in gaap['WeightedAverageNumberOfSharesOutstandingBasic'] and 'shares' in gaap['WeightedAverageNumberOfSharesOutstandingBasic']['units']:
            shares_data = gaap['WeightedAverageNumberOfSharesOutstandingBasic']['units']['shares']
            if shares_data:
                # Get the most recent entry
                basic_shares = shares_data[-1]['val']
        
        # Extract diluted shares data if available
        diluted_shares = None
        if 'WeightedAverageNumberOfDilutedSharesOutstanding' in gaap and 'units' in gaap['WeightedAverageNumberOfDilutedSharesOutstanding'] and 'shares' in gaap['WeightedAverageNumberOfDilutedSharesOutstanding']['units']:
            shares_data = gaap['WeightedAverageNumberOfDilutedSharesOutstanding']['units']['shares']
            if shares_data:
                # Get the most recent entry
                diluted_shares = shares_data[-1]['val']
        
        # Calculate dilution percentage if both values are available
        dilution_percentage = None
        if basic_shares is not None and diluted_shares is not None and basic_shares > 0:
            additional_shares = diluted_shares - basic_shares
            dilution_percentage = (additional_shares / basic_shares) * 100
            
            # Log the share information for debugging
            logger.info(f"{stock.symbol} shares - Basic: {basic_shares:,}, Diluted: {diluted_shares:,}, Dilution: {dilution_percentage:.3f}%")
        
        return basic_shares, diluted_shares, dilution_percentage
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.warning(f"Rate limit hit for CIK {stock.cik}. Retrying after delay...")
            time.sleep(random.uniform(5, 10))
            
            try:
                throttle_requests()
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                
                # Process response after successful retry (simplified)
                data = response.json()
                if 'facts' in data and 'us-gaap' in data['facts']:
                    # This is a simplified retry - in production you might want to refactor to avoid code duplication
                    return None, None, None
                    
            except Exception as retry_e:
                logger.error(f"Retry failed for CIK {stock.cik}: {str(retry_e)}")
                return None, None, None
        else:
            logger.error(f"HTTP error fetching company facts for CIK {stock.cik}: {str(e)}")
            return None, None, None
    except Exception as e:
        logger.error(f"Error fetching company facts for CIK {stock.cik}: {str(e)}")
        return None, None, None

def enhance_stock_with_submission_data(stock: Stock) -> Stock:
    """Enhance a Stock object with detailed submission data and company facts."""
    try:
        # Fetch detailed data
        submission_data = fetch_sec_submission_data(stock)
        
        if not submission_data:
            logger.warning(f"No submission data found for {stock.symbol} (CIK: {stock.cik})")
            return stock
        
        # Fetch company facts data for shares information
        basic_shares, diluted_shares, dilution_percentage = fetch_sec_company_facts(stock)
        
        # Add share data to submission data
        if basic_shares is not None:
            submission_data['basicShares'] = basic_shares
        if diluted_shares is not None:
            submission_data['dilutedShares'] = diluted_shares
        if dilution_percentage is not None:
            submission_data['dilutionPercentage'] = dilution_percentage
            
        # Create a new Stock object with enhanced data
        enhanced_stock = Stock.update_from_submission(stock, submission_data)
        return enhanced_stock
    except Exception as e:
        logger.error(f"Error enhancing stock {stock.symbol}: {str(e)}")
        return stock

def enhance_stocks_parallel(stocks: List[Stock], max_workers: int = 2) -> List[Stock]:
    """Enhance multiple Stock objects with submission data in parallel."""
    enhanced_stocks = []
    total = len(stocks)
    
    logger.info(f"Enhancing {total} stocks with detailed submission data using {max_workers} workers")
    
    # Use a smaller number of workers to avoid overwhelming the API
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs but monitor closely
        futures = []
        for stock in stocks:
            futures.append(executor.submit(enhance_stock_with_submission_data, stock))
        
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                enhanced_stock = future.result()
                enhanced_stocks.append(enhanced_stock)
                
                completed += 1
                if completed % 10 == 0 or completed == total:
                    logger.info(f"Progress: {completed}/{total} stocks enhanced ({completed/total:.1%})")
                
            except Exception as e:
                logger.error(f"Error processing stock: {str(e)}")
    
    return enhanced_stocks

def load_to_supabase(stocks: List[Stock], table: str = 'stocks'):
    """Load the processed data into Supabase."""
    try:
        # Convert objects to dictionaries with proper JSON serialization
        records = []
        for stock in stocks:
            # Use model_dump() with exclude_none to avoid null values and handle datetime serialization
            stock_dict = stock.model_dump(exclude_none=True)
            
            # No special handling needed for former_names now that it's correctly typed as List[Dict]
            # It will be automatically serialized correctly
            
            records.append(stock_dict)
        
        # Insert in batches to avoid timeout
        batch_size = 1000
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            logger.info(f"Inserting batch {i//batch_size + 1} of {(len(records) + batch_size - 1) // batch_size} ({len(batch)} records)")
            
            try:
                supabase.table(table).upsert(batch).execute()
            except Exception as e:
                logger.error(f"Error inserting batch: {str(e)}")
                
                # If batch insert fails, try one by one
                logger.info("Attempting to insert records one by one")
                for record in batch:
                    try:
                        supabase.table(table).upsert([record]).execute()
                    except Exception as e:
                        symbol = record.get('symbol', 'unknown')
                        logger.error(f"Failed to insert record {symbol}: {str(e)}")
        
        logger.info(f"Successfully loaded {len(records)} records into Supabase")
    except Exception as e:
        logger.error(f"Error loading data to Supabase: {str(e)}")
        raise

def main():
    """Main function to fetch SEC data and load it into Supabase."""
    try:
        # STEP 1: Fetch basic ticker data
        basic_stocks = fetch_sec_tickers()
        
        if not basic_stocks:
            logger.warning("No data fetched from SEC tickers endpoint, aborting")
            return
        
        # STEP 2: Enhance with detailed submission data
        # For testing, you can limit the number of stocks to enhance
        max_stocks_to_enhance = int(os.getenv("MAX_STOCKS_TO_ENHANCE", len(basic_stocks)))
        stocks_to_enhance = basic_stocks[:max_stocks_to_enhance]
        
        logger.info(f"Enhancing {len(stocks_to_enhance)} out of {len(basic_stocks)} stocks with detailed data")
        enhanced_stocks = enhance_stocks_parallel(stocks_to_enhance)
            
        # STEP 3: Load data into Supabase
        load_to_supabase(enhanced_stocks)
        
        logger.info("Data loading completed successfully")
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main() 