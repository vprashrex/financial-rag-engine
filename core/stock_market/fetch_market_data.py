"""
1. connect to financial data and fetch atleast 5 stocks data/cryptos data
2. process incoming data with timestamps and proper data validation
3. calculate moving averages, RSI, volatility metrics.
5. print the data in a readable format
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from logger import stock_logger as logger
from langchain.schema import Document
from uuid import uuid4
load_dotenv()

        
class MarketDataAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
    
    def fetch_stock_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch daily stock data from Alpha Vantage"""
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'compact'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # Check for API errors
            if 'Information' in data:
                logger.error(f"API Error for {symbol}: {data['Information']}")
                return None

            if 'Time Series (Daily)' not in data:
                logger.error(f"No time series data for {symbol}")
                return None
            
            # Convert to DataFrame
            time_series = data['Time Series (Daily)']
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Clean column names and convert to float
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.astype(float)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Add metadata
            df['Symbol'] = symbol
            df['Timestamp'] = df.index
            df['Fetch_Time'] = datetime.now()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {str(e)}")
            return None
    
    def fetch_crypto_data(self, symbol: str, market: str = 'USD') -> Optional[pd.DataFrame]:
        """Fetch daily crypto data from Alpha Vantage"""
        params = {
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': symbol,
            'market': market,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # Check for API errors
            if 'Information' in data:
                logger.error(f"API Error for {symbol}: {data['Information']}")
                return None
            
            if 'Note' in data:
                logger.error(f"Rate limit reached for {symbol}: {data['Note']}")
                return None
                
            if 'Time Series (Digital Currency Daily)' not in data:
                logger.error(f"No crypto data for {symbol}")
                return None
            
            # Convert to DataFrame
            time_series = data['Time Series (Digital Currency Daily)']
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Debug: Print actual column names to see what's available
            logger.debug(f"Available columns for {symbol}: {df.columns.tolist()}")
            
            try:
                # Try to extract the needed columns with more flexible approach
                open_col = next((col for col in df.columns if f'open ({market.lower()})' in col.lower()), None)
                high_col = next((col for col in df.columns if f'high ({market.lower()})' in col.lower()), None)
                low_col = next((col for col in df.columns if f'low ({market.lower()})' in col.lower()), None)
                close_col = next((col for col in df.columns if f'close ({market.lower()})' in col.lower()), None)
                volume_col = next((col for col in df.columns if 'volume' in col.lower()), None)
                
                if not all([open_col, high_col, low_col, close_col, volume_col]):
                    # As a fallback, use numerical indices based on the actual column structure
                    # Column structure appears to be: '1. open', '2. high', '3. low', '4. close', '5. volume'
                    result_df = pd.DataFrame({
                        'Open': pd.to_numeric(df.iloc[:, 0], errors='coerce'),
                        'High': pd.to_numeric(df.iloc[:, 1], errors='coerce'),
                        'Low': pd.to_numeric(df.iloc[:, 2], errors='coerce'),
                        'Close': pd.to_numeric(df.iloc[:, 3], errors='coerce'),
                        'Volume': pd.to_numeric(df.iloc[:, 4], errors='coerce')
                    }, index=df.index)
                else:
                    # If we found all columns, use them
                    result_df = pd.DataFrame({
                        'Open': pd.to_numeric(df[open_col], errors='coerce'),
                        'High': pd.to_numeric(df[high_col], errors='coerce'),
                        'Low': pd.to_numeric(df[low_col], errors='coerce'),
                        'Close': pd.to_numeric(df[close_col], errors='coerce'),
                        'Volume': pd.to_numeric(df[volume_col], errors='coerce')
                    }, index=df.index)
                    
                result_df.index = pd.to_datetime(result_df.index)
                result_df = result_df.sort_index()
                
                # Add metadata
                result_df['Symbol'] = f"{symbol}-{market}"
                result_df['Timestamp'] = result_df.index
                result_df['Fetch_Time'] = datetime.now()
                
                return result_df
                
            except Exception as e:
                logger.error(f"Error processing crypto data for {symbol}: {str(e)}")
                logger.error(f"Columns in response: {df.columns.tolist()}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching crypto {symbol}: {str(e)}")
            return None

    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate market data"""
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check if all required columns exist
        if not all(col in df.columns for col in required_columns):
            return False
            
        # Check for null values in price data
        if df[required_columns[:-1]].isnull().any().any():  # Exclude Volume from null check
            return False
            
        # Check for negative prices
        price_columns = ['Open', 'High', 'Low', 'Close']
        if (df[price_columns] <= 0).any().any():
            return False
            
        # Check if High >= Low
        if (df['High'] < df['Low']).any():
            return False
            
        return True

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages, RSI, and volatility metrics"""
        # Moving Averages
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_10'] = df['Close'].rolling(window=10).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        
        # RSI calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Volatility metrics
        df['Returns'] = df['Close'].pct_change()
        df['Volatility'] = df['Returns'].rolling(window=20).std() * np.sqrt(252)  # Annualized
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # Average True Range (ATR)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        return df

    def fetch_market_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch data for selected stocks and cryptos"""
        # Select representative stocks from different sectors
        stocks = [
            'AAPL',
            'MSFT',
            'JPM'
        ]

        cryptos = [
            'BTC',
            'ETH'
        ]
        
        data = {}
        
        logger.debug("Fetching stock data...")
        for symbol in stocks:
            df = self.fetch_stock_data(symbol)
            if df is not None and self.validate_data(df):
                df = self.calculate_indicators(df)
                data[symbol] = df
                logger.debug(f"Successfully processed {symbol}")
        
        logger.debug("\nFetching crypto data...")
        for symbol in cryptos:
            df = self.fetch_crypto_data(symbol)
            if df is not None and self.validate_data(df):
                df = self.calculate_indicators(df)
                data[f"{symbol}-USD"] = df
                logger.debug(f"Successfully processed {symbol}")
        
        return data

    def generate_summary_report(self, data: Dict[str, pd.DataFrame]) -> str:
        """Generate market data summary in markdown format"""
        try:
            documents = []
            market_id = str(uuid4())
            # markdown_output.append(f"# Market Analysis Report\n")
            # markdown_output.append(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            # markdown_output.append(f"Total Symbols: {len(data)}\n")
            
            for symbol, df in data.items():
                if not df.empty:
                    latest = df.iloc[-1]
                    markdown_output = ""
                    markdown_output += f"\n## {symbol}\n"
                    markdown_output += f"- Price: ${latest['Close']:.2f}\n"
                    markdown_output += f"- Volume: {latest['Volume']:,.0f}\n"
                    markdown_output += f"- Daily Change: {((latest['Close'] - latest['Open']) / latest['Open'] * 100):+.2f}%\n"
                    
                    # Technical Indicators
                    markdown_output += f"\n### Technical Indicators:\n"
                    if pd.notna(latest['MA_5']):
                        markdown_output += f"- MA(5): ${latest['MA_5']:.2f}\n"
                    if pd.notna(latest['MA_20']):
                        markdown_output+= f"- MA(20): ${latest['MA_20']:.2f}\n"
                    if pd.notna(latest['RSI']):
                        markdown_output += f"- RSI: {latest['RSI']:.1f}"
                        if latest['RSI'] > 70:
                            markdown_output += f" *Overbought Signal*"
                        elif latest['RSI'] < 30:
                            markdown_output += f" *Oversold Signal*"
                        markdown_output += f"\n"
                    if pd.notna(latest['Volatility']):
                        markdown_output += f"- Volatility: {latest['Volatility']:.1%}\n"
                    if pd.notna(latest['ATR']):
                        markdown_output += f"- ATR: ${latest['ATR']:.2f}\n"
                    
                    markdown_output += f"\nLast Update: {latest['Timestamp'].strftime('%Y-%m-%d')}\n"
                    documents.append(
                        Document(
                            page_content=markdown_output,
                            metadata={
                                'id': market_id, # Unique ID for the report
                                'symbol': symbol,
                                'timestamp': latest['Timestamp'].strftime('%Y-%m-%d'),
                            }
                        )
                    )
            
            return documents
        except Exception as e:
            logger.error(f"Error generating summary report: {str(e)}")
            return "Error generating summary report"
        
# if __name__ == "__main__":
#     analyzer = MarketDataAnalyzer()
#     market_data = analyzer.fetch_market_data()
#     print("Market data fetched successfully. You can now generate a summary report or process the data further.")
#     summary_report = analyzer.generate_summary_report(market_data)
#     print(summary_report)