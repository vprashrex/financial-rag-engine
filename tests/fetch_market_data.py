"""
1. connect to financial data and fetch atleast 5 stocks data/cryptos data
2. process incoming data with timestamps and proper data validation
3. calculate moving averages, RSI, volatility metrics.
5. print the data in a readable format
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
from typing import Dict, Optional
from dotenv import load_dotenv
load_dotenv()

class MarketDataFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
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
            if 'Error Message' in data:
                print(f"✗ API Error for {symbol}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                print(f"✗ Rate limit reached for {symbol}: {data['Note']}")
                return None
                
            if 'Time Series (Daily)' not in data:
                print(f"✗ No time series data for {symbol}")
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
            print(f"✗ Error fetching {symbol}: {str(e)}")
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
            if 'Error Message' in data:
                print(f"✗ API Error for {symbol}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                print(f"✗ Rate limit reached for {symbol}: {data['Note']}")
                return None
                
            if 'Time Series (Digital Currency Daily)' not in data:
                print(f"✗ No crypto data for {symbol}")
                return None
            
            # Convert to DataFrame
            time_series = data['Time Series (Digital Currency Daily)']
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Debug: Print actual column names to see what's available
            print(f"Available columns for {symbol}: {df.columns.tolist()}")
            
            try:
                # Try to extract the needed columns with more flexible approach
                open_col = next((col for col in df.columns if f'open ({market.lower()})' in col.lower()), None)
                high_col = next((col for col in df.columns if f'high ({market.lower()})' in col.lower()), None)
                low_col = next((col for col in df.columns if f'low ({market.lower()})' in col.lower()), None)
                close_col = next((col for col in df.columns if f'close ({market.lower()})' in col.lower()), None)
                volume_col = next((col for col in df.columns if 'volume' in col.lower()), None)
                
                if not all([open_col, high_col, low_col, close_col, volume_col]):
                    # As a fallback, use numerical indices if we can't find the columns by name
                    result_df = pd.DataFrame({
                        'Open': pd.to_numeric(df.iloc[:, 0], errors='coerce'),
                        'High': pd.to_numeric(df.iloc[:, 2], errors='coerce'),
                        'Low': pd.to_numeric(df.iloc[:, 4], errors='coerce'),
                        'Close': pd.to_numeric(df.iloc[:, 6], errors='coerce'),
                        'Volume': pd.to_numeric(df.iloc[:, 8], errors='coerce')
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
                print(f"✗ Error processing crypto data for {symbol}: {str(e)}")
                print(f"Columns in response: {df.columns.tolist()}")
                return None
                
        except Exception as e:
            print(f"✗ Error fetching crypto {symbol}: {str(e)}")
            return None

def validate_data(df: pd.DataFrame) -> bool:
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

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
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

def fetch_market_data() -> Dict[str, pd.DataFrame]:
    """Fetch data for selected stocks and cryptos"""

    api_key = os.getenv("VANTAGE_API_KEY")
    
    fetcher = MarketDataFetcher(api_key)
    
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
    
    print("📈 Fetching stock data...")
    for symbol in stocks:
        df = fetcher.fetch_stock_data(symbol)
        if df is not None and validate_data(df):
            df = calculate_indicators(df)
            data[symbol] = df
            print(f"✓ Successfully processed {symbol}")
        
        # Respect API rate limits (5 calls per minute for free tier)
        #time.sleep(12)  # Wait 12 seconds between calls
    
    print("\n₿ Fetching crypto data...")
    for symbol in cryptos:
        df = fetcher.fetch_crypto_data(symbol)
        if df is not None and validate_data(df):
            df = calculate_indicators(df)
            data[f"{symbol}-USD"] = df
            print(f"✓ Successfully processed {symbol}")
        
        # Respect API rate limits
        #time.sleep(12)
    
    return data

def print_summary(data: Dict[str, pd.DataFrame]):
    """Print data in readable format"""
    print("\n" + "="*80)
    print("📊 ALPHA VANTAGE MARKET DATA SUMMARY")
    print("="*80)
    print(f"🕐 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📈 Total Symbols: {len(data)}")
    
    for symbol, df in data.items():
        if not df.empty:
            latest = df.iloc[-1]
            
            print(f"\n📊 {symbol}")
            print(f"   💰 Price: ${latest['Close']:.2f}")
            print(f"   📊 Volume: {latest['Volume']:,.0f}")
            print(f"   📈 Daily Change: {((latest['Close'] - latest['Open']) / latest['Open'] * 100):+.2f}%")
            
            # Technical Indicators
            print(f"   📉 Technical Indicators:")
            if pd.notna(latest['MA_5']):
                print(f"      • MA(5):  ${latest['MA_5']:.2f}")
            if pd.notna(latest['MA_20']):
                print(f"      • MA(20): ${latest['MA_20']:.2f}")
            if pd.notna(latest['RSI']):
                print(f"      • RSI: {latest['RSI']:.1f}")
                if latest['RSI'] > 70:
                    print(f"        🔴 Overbought Signal")
                elif latest['RSI'] < 30:
                    print(f"        🟢 Oversold Signal")
            if pd.notna(latest['Volatility']):
                print(f"      • Volatility: {latest['Volatility']:.1%}")
            if pd.notna(latest['ATR']):
                print(f"      • ATR: ${latest['ATR']:.2f}")
            
            print(f"   🕐 Last Update: {latest['Timestamp'].strftime('%Y-%m-%d')}")

def main():
    try:
        print("🚀 Fetching live market data from Alpha Vantage...")
        market_data = fetch_market_data()
        
        if market_data:
            print_summary(market_data)
        else:
            print("❌ No data was successfully fetched")
            
    except KeyboardInterrupt:
        print("\n❌ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()