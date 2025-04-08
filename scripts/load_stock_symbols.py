import os
import pandas as pd
from ftplib import FTP
from supabase import create_client
from dotenv import load_dotenv
import logging
from typing import Dict, List, Callable, Any
from io import BytesIO, StringIO
from src.models import Stock

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

FTP_HOST = "ftp.nasdaqtrader.com"
REMOTE_DIR = "/SymbolDirectory"

def download_file(filename: str) -> pd.DataFrame:
    """Download and parse a stock symbol file from NASDAQ FTP."""
    try:
        logger.info(f"Downloading {filename}")
        
        # Connect to FTP server
        ftp = FTP(FTP_HOST)
        ftp.login()  # Anonymous login

        # Change to the correct directory
        ftp.cwd(REMOTE_DIR)
        
        # Download file content
        bytes_buffer = BytesIO()
        ftp.retrbinary(f'RETR {filename}', bytes_buffer.write)
        ftp.quit()
        
        # Read the data into a DataFrame
        text_data = bytes_buffer.getvalue().decode("utf-8")
        df = pd.read_csv(StringIO(text_data), sep='|')
        
        # Clean up column names (remove spaces and convert to lowercase)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        return df
    except Exception as e:
        logger.error(f"Error downloading {filename}: {str(e)}")
        raise

def transform_data(df: pd.DataFrame, transformer: Callable[[pd.Series], Stock]) -> List[Dict]:
    """Transform data using the provided transformer function."""
    try:
        # Convert each row to a Stock instance
        stocks = []
        for _, row in df.iterrows():
            stock = transformer(row)
            if stock is not None:
                stocks.append(stock)
        
        # Log the number of valid records
        logger.info(f"Successfully transformed {len(stocks)} records out of {len(df)} rows")
        
        # Convert to list of dictionaries for Supabase
        return [stock.model_dump() for stock in stocks]
    except Exception as e:
        logger.error(f"Error transforming data: {str(e)}")
        raise

def load_to_supabase(records: List[Dict], table: str = 'stocks'):
    """Load the transformed data into Supabase."""
    try:
        # Insert in batches to avoid timeout
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            logger.info(f"Inserting batch {i//batch_size + 1}")
            try:
                supabase.table(table).insert(batch, upsert=True).execute()
            except Exception as e:
                # If batch insert fails, try inserting records one by one
                logger.warning(f"Batch insert failed, trying individual records: {str(e)}")
                for record in batch:
                    try:
                        supabase.table(table).insert(record, upsert=True).execute()
                    except Exception as e:
                        logger.warning(f"Failed to insert record {record['symbol']} on {record['exchange']}: {str(e)}")
                        continue
            
    except Exception as e:
        logger.error(f"Error loading data to Supabase: {str(e)}")
        raise

def process_file(file_info: Dict[str, Any]) -> None:
    """Process a single file based on its configuration."""
    filename = file_info['filename']
    transformer = file_info['transformer']
    logger.info(f"Processing {filename}...")
    
    try:
        df = download_file(filename)
        records = transform_data(df, transformer)
        load_to_supabase(records)
        logger.info(f"Successfully processed {filename}")
    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        raise

def main():
    """Main function to download and process stock symbol data."""
    # Define file configurations
    files_to_process = [
        {
            'filename': 'otherlisted.txt',
            'transformer': Stock.from_other_listed,
            'description': 'Other exchange listed stocks'
        },
        {
            'filename': 'nasdaqlisted.txt',
            'transformer': Stock.from_nasdaq_listed,
            'description': 'NASDAQ listed stocks'
        }
    ]
    
    # Process each file
    for file_info in files_to_process:
        process_file(file_info)
        
    logger.info("Data loading completed successfully")

if __name__ == "__main__":
    main() 