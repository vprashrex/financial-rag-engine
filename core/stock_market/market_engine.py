"""
1. fetch market data from the vantage API
2. process the market data information and generate the summary report
3. store the market data in SQLite database
4. use LangChain SQL agent for intelligent querying
"""

import sqlite3
from datetime import datetime
import os
from datetime import datetime
from pathlib import Path
from core.stock_market.fetch_market_data import MarketDataAnalyzer
from logger import stock_logger as logger
from typing import List, Dict, Any, Optional
import pandas as pd

# Updated LangChain imports (fixed deprecation warnings)
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import (
    create_sql_agent,
)  # Updated import
from langchain.agents.agent_types import AgentType
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
)  # Updated memory handling
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from enum import Enum

load_dotenv()


class StockQueryIntent(str, Enum):
    price = "price"
    trend = "trend"
    comparison = "comparison"
    volume = "volume"
    volatility = "volatility"
    technical = "technical"  # For MA, RSI, ATR
    change = "change"
    other = "other"


class StockQueryExtraction(BaseModel):
    symbols: List[str]
    intent: Optional[StockQueryIntent] = None
    time_range: Optional[str] = None
    metrics: Optional[List[str]] = None  # Should match: close, rsi, ma5, atr, etc.
    aggregation: Optional[str] = None  # avg, max, min, etc.


class MarketEngine:
    def __init__(self, db_path: str = "market_data.db"):
        self.market_data_service = MarketDataAnalyzer()
        self.db_path = db_path
        self.init_db()
        self._setup_sql_agent()

    def init_db(self):
        """Initialize SQLite database for market data storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create stock_data table with specified structure
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS stock_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,               -- e.g., "AAPL", "BTC-USD"
                        timestamp TEXT NOT NULL,            -- ISO format datetime
                        open REAL,                          -- Market open price
                        high REAL,                          -- High price
                        low REAL,                           -- Low price
                        close REAL,                         -- Closing price
                        volume INTEGER,                     -- Trade volume
                        ma5 REAL,                           -- 5-period moving average
                        ma10 REAL,                          -- 10-period moving average
                        ma20 REAL,                          -- 20-period moving average
                        rsi REAL,                           -- Relative Strength Index
                        volatility REAL,                    -- Volatility metric
                        atr REAL,                           -- Average True Range
                        pct_change REAL,                    -- % change from previous close
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes for faster queries
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON stock_data(symbol, timestamp)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_symbol ON stock_data(symbol)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_timestamp ON stock_data(timestamp)"
                )

                conn.commit()
                logger.info("Stock data database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing stock data database: {str(e)}")
            raise

    def _setup_sql_agent(self):
        """Setup LangChain SQL agent for intelligent querying"""
        try:
            # Initialize Google Generative AI
            self.llm = GoogleGenerativeAI(
                model="gemini-2.5-flash-preview-05-20",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1,
            )

            # Create SQLDatabase connection
            db_uri = f"sqlite:///{self.db_path}"
            self.db = SQLDatabase.from_uri(db_uri)

            # Create SQL toolkit
            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)

            # Initialize conversation history (updated approach)
            self.conversation_history = []

            # Create SQL agent with updated import
            self.sql_agent = create_sql_agent(
                llm=self.llm,
                toolkit=toolkit,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=False,
                handle_parsing_errors=True,
                max_iterations=5,
                early_stopping_method="generate",
            )

            logger.info("SQL agent initialized successfully")

        except Exception as e:
            logger.error(f"Error setting up SQL agent: {str(e)}")
            # Fallback to None if agent setup fails
            self.sql_agent = None

    def fetch_and_update_market_data(self):
        """
        Fetch market data and store in SQLite database.
        """
        try:
            # Fetch market data
            market_data = self.market_data_service.fetch_market_data()
            if not market_data:
                logger.error("No market data found")
                raise ValueError("No market data found")

            # Store in SQLite database
            records_stored = self._store_market_data(market_data)

            logger.info(
                f"Successfully stored {records_stored} market data records in SQLite database"
            )
            return {
                "status": "success",
                "code": 200,
                "message": f"Successfully updated market data - {records_stored} records stored",
            }

        except Exception as e:
            logger.error(f"Error fetching or updating market data: {str(e)}")
            raise

    def _store_market_data(self, market_data: Dict[str, pd.DataFrame]) -> int:
        """Store market data in SQLite database"""
        try:
            records_stored = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for symbol, df in market_data.items():
                    if df.empty:
                        continue

                    # Calculate percentage change for the dataframe
                    df["pct_change"] = df["Close"].pct_change() * 100

                    # Store each row as a separate record
                    for index, row in df.iterrows():
                        # Convert timestamp to ISO format
                        timestamp_iso = (
                            row["Timestamp"].isoformat()
                            if pd.notna(row["Timestamp"])
                            else index.isoformat()
                        )

                        # Prepare data for insertion
                        stock_record = (
                            symbol,  # symbol
                            timestamp_iso,  # timestamp
                            (
                                float(row["Open"]) if pd.notna(row["Open"]) else None
                            ),  # open
                            (
                                float(row["High"]) if pd.notna(row["High"]) else None
                            ),  # high
                            float(row["Low"]) if pd.notna(row["Low"]) else None,  # low
                            (
                                float(row["Close"]) if pd.notna(row["Close"]) else None
                            ),  # close
                            (
                                int(row["Volume"]) if pd.notna(row["Volume"]) else None
                            ),  # volume
                            (
                                float(row["MA_5"]) if pd.notna(row["MA_5"]) else None
                            ),  # ma5
                            (
                                float(row["MA_10"]) if pd.notna(row["MA_10"]) else None
                            ),  # ma10
                            (
                                float(row["MA_20"]) if pd.notna(row["MA_20"]) else None
                            ),  # ma20
                            float(row["RSI"]) if pd.notna(row["RSI"]) else None,  # rsi
                            (
                                float(row["Volatility"])
                                if pd.notna(row["Volatility"])
                                else None
                            ),  # volatility
                            float(row["ATR"]) if pd.notna(row["ATR"]) else None,  # atr
                            (
                                float(row["pct_change"])
                                if pd.notna(row["pct_change"])
                                else None
                            ),  # pct_change
                            datetime.now().isoformat(),  # updated_at
                        )

                        # Insert or replace record
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO stock_data 
                            (symbol, timestamp, open, high, low, close, volume, 
                             ma5, ma10, ma20, rsi, volatility, atr, pct_change, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            stock_record,
                        )

                        records_stored += 1

                conn.commit()
                logger.info(f"Stored {records_stored} stock data records in SQLite")
                return records_stored

        except Exception as e:
            logger.error(f"Error storing market data: {str(e)}")
            raise

    def _build_dynamic_sql_query(
        self, extraction: StockQueryExtraction
    ) -> tuple[str, list]:
        """
        Build SQL query dynamically based on the extracted query structure

        Args:
            extraction: StockQueryExtraction object with symbols, intent, time_range, etc.

        Returns:
            Tuple of (sql_query, parameters)
        """
        # Base SELECT clause
        select_columns = ["symbol", "timestamp"]

        # Determine columns based on intent and metrics
        if extraction.metrics:
            # Add specific requested metrics
            select_columns.extend(extraction.metrics)
        else:
            # Default columns based on intent
            if extraction.intent == StockQueryIntent.price:
                select_columns.extend(["open", "high", "low", "close"])
            elif extraction.intent == StockQueryIntent.volume:
                select_columns.extend(["volume", "close"])
            elif extraction.intent == StockQueryIntent.volatility:
                select_columns.extend(["volatility", "close", "atr"])
            elif extraction.intent == StockQueryIntent.technical:
                select_columns.extend(["ma5", "ma10", "ma20", "rsi", "atr"])
            elif extraction.intent == StockQueryIntent.trend:
                select_columns.extend(["close", "ma5", "ma20", "pct_change"])
            elif extraction.intent == StockQueryIntent.comparison:
                select_columns.extend(["close", "rsi", "ma5", "ma20", "volume"])
            elif extraction.intent == StockQueryIntent.change:
                select_columns.extend(["close", "pct_change", "open"])
            else:
                # Default comprehensive view
                select_columns.extend(["open", "high", "low", "close", "volume"])

        # Remove duplicates while preserving order
        select_columns = list(dict.fromkeys(select_columns))
        select_clause = ", ".join(select_columns)

        # Apply aggregation if specified
        if extraction.aggregation:
            agg_columns = []
            for col in select_columns:
                if col in ["symbol", "timestamp"]:
                    if extraction.aggregation in ["avg", "sum", "max", "min"]:
                        continue  # Skip non-numeric columns for aggregation
                    agg_columns.append(col)
                else:
                    agg_func = extraction.aggregation.upper()
                    agg_columns.append(f"{agg_func}({col}) as {agg_func.lower()}_{col}")

            if extraction.aggregation in ["avg", "sum", "max", "min"]:
                # Group by symbol for aggregations
                select_clause = f"symbol, {', '.join(agg_columns[1:])}"  # Skip symbol in agg_columns
            else:
                select_clause = ", ".join(agg_columns)

        # Handle multiple symbols with proper limiting for comparisons
        if extraction.intent == StockQueryIntent.comparison and len(extraction.symbols or []) > 1:
            # For comparisons with multiple symbols, we need to ensure balanced results
            # Use a special approach for SQLite that works without CTEs or window functions
            
            # Set records per symbol
            records_per_symbol = 25  # Adjust as needed
            
            # We'll run a separate query for each symbol using Python
            sql_query = f"SELECT {select_clause} FROM stock_data WHERE symbol = ?"
            
            # Add time range filter if present
            if extraction.time_range:
                time_condition, time_params = self._build_time_filter(extraction.time_range)
                if time_condition:
                    sql_query += f" AND {time_condition}"
                    # We'll handle params differently - see execute_dynamic_query
            
            # Add ordering and limit for each symbol's query
            sql_query += f" ORDER BY timestamp DESC LIMIT {records_per_symbol}"
            
            # Return special marker to indicate this is a multi-query scenario
            # We'll handle this specially in execute_dynamic_query
            return sql_query, extraction.symbols, True  # Return tuple with third element as multi-query flag
            
        else:
            # Build WHERE clause for regular queries
            where_conditions = []
            params = []

            # Symbol filter
            if extraction.symbols:
                symbol_placeholders = ", ".join(["?" for _ in extraction.symbols])
                where_conditions.append(f"symbol IN ({symbol_placeholders})")
                params.extend(extraction.symbols)

            # Time range filter
            if extraction.time_range:
                time_condition, time_params = self._build_time_filter(extraction.time_range)
                if time_condition:
                    where_conditions.append(time_condition)
                    params.extend(time_params)

            # Construct regular query for single symbol or non-comparison queries
            sql_query = f"SELECT {select_clause} FROM stock_data"

            if where_conditions:
                sql_query += f" WHERE {' AND '.join(where_conditions)}"

            # Add GROUP BY for aggregations
            if extraction.aggregation and extraction.aggregation in [
                "avg",
                "sum",
                "max",
                "min",
            ]:
                sql_query += " GROUP BY symbol"

            # Add ORDER BY
            sql_query += " ORDER BY timestamp DESC"

            # Add LIMIT for performance
            if not extraction.aggregation:
                sql_query += " LIMIT 50"

            return sql_query, params, False  # Regular single query

    def _build_time_filter(self, time_range: str) -> tuple[str, list]:
        """
        Build time filter condition based on time range string

        Args:
            time_range: Time range string like "today", "last week", "this month", etc.

        Returns:
            Tuple of (condition_string, parameters)
        """
        time_range_lower = time_range.lower()

        # Map time ranges to SQLite datetime expressions
        time_filters = {
            "today": ("timestamp >= date('now')", []),
            "yesterday": (
                "timestamp >= date('now', '-1 day') AND timestamp < date('now')",
                [],
            ),
            "last week": ("timestamp >= date('now', '-7 days')", []),
            "this week": ("timestamp >= date('now', 'weekday 0', '-6 days')", []),
            "last month": ("timestamp >= date('now', '-1 month')", []),
            "this month": ("timestamp >= date('now', 'start of month')", []),
            "last year": ("timestamp >= date('now', '-1 year')", []),
            "this year": ("timestamp >= date('now', 'start of year')", []),
        }

        # Check for numeric day patterns like "7 days", "30 days"
        import re

        day_pattern = re.match(r"(\d+)\s*days?", time_range_lower)
        if day_pattern:
            days = int(day_pattern.group(1))
            return f"timestamp >= date('now', '-{days} days')", []

        # Check for week patterns
        week_pattern = re.match(r"(\d+)\s*weeks?", time_range_lower)
        if week_pattern:
            weeks = int(week_pattern.group(1))
            days = weeks * 7
            return f"timestamp >= date('now', '-{days} days')", []

        # Check for month patterns
        month_pattern = re.match(r"(\d+)\s*months?", time_range_lower)
        if month_pattern:
            months = int(month_pattern.group(1))
            return f"timestamp >= date('now', '-{months} months')", []

        return time_filters.get(time_range_lower, ("", []))

    def execute_dynamic_query(self, extraction: StockQueryExtraction) -> Dict[str, Any]:
        """
        Execute the dynamically built SQL query and return results
        
        Args:
            extraction: StockQueryExtraction object
            
        Returns:
            Dictionary with query results and metadata
        """
        try:
            # Build the SQL query
            query_result = self._build_dynamic_sql_query(extraction)
            
            # Check if this is a multi-query scenario (for comparison with multiple symbols)
            if len(query_result) == 3:
                sql_query, symbols, is_multi_query = query_result
                
                if is_multi_query:
                    logger.info(f"Executing multi-symbol query for comparison")
                    
                    # Execute separate queries for each symbol and combine results
                    all_data = []
                    
                    for symbol in symbols:
                        # For each symbol, execute the base query with this symbol's parameters
                        params = [symbol]
                        
                        # Add time params if needed
                        if extraction.time_range:
                            _, time_params = self._build_time_filter(extraction.time_range)
                            params.extend(time_params)
                        
                        logger.info(f"Executing query for symbol {symbol}: {sql_query}")
                        logger.info(f"Parameters: {params}")
                        
                        with sqlite3.connect(self.db_path) as conn:
                            conn.row_factory = sqlite3.Row
                            cursor = conn.cursor()
                            
                            cursor.execute(sql_query, params)
                            symbol_results = cursor.fetchall()
                            
                            # Convert to list of dictionaries and add to combined results
                            all_data.extend([dict(row) for row in symbol_results])
                    
                    # Sort combined results by symbol and timestamp
                    all_data.sort(key=lambda x: (x.get('symbol', ''), x.get('timestamp', '')), reverse=True)
                    
                    # Generate summary based on intent
                    summary = self._generate_result_summary(extraction, all_data)
                    
                    return {
                        "status": "success",
                        "query_info": {
                            "symbols": extraction.symbols,
                            "intent": extraction.intent.value if extraction.intent else None,
                            "time_range": extraction.time_range,
                            "metrics": extraction.metrics,
                            "aggregation": extraction.aggregation
                        },
                        "sql_query": f"Multiple queries executed for {len(symbols)} symbols: {sql_query}",
                        "record_count": len(all_data),
                        "data": all_data,
                        "summary": summary,
                        "timestamp": datetime.now().isoformat()
                    }
                
            # Regular single query execution
            sql_query, params = query_result[:2]
            
            logger.info(f"Generated SQL: {sql_query}")
            logger.info(f"Parameters: {params}")
            
            # Execute query
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(sql_query, params)
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                data = [dict(row) for row in results]
                
                # Generate summary based on intent
                summary = self._generate_result_summary(extraction, data)
                
                return {
                    "status": "success",
                    "query_info": {
                        "symbols": extraction.symbols,
                        "intent": extraction.intent.value if extraction.intent else None,
                        "time_range": extraction.time_range,
                        "metrics": extraction.metrics,
                        "aggregation": extraction.aggregation
                    },
                    "sql_query": sql_query,
                    "record_count": len(data),
                    "data": data,
                    "summary": summary,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error executing dynamic query: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "query_info": {
                    "symbols": extraction.symbols,
                    "intent": extraction.intent.value if extraction.intent else None,
                    "time_range": extraction.time_range
                },
                "timestamp": datetime.now().isoformat()
            }

    def _generate_result_summary(
        self, extraction: StockQueryExtraction, data: List[Dict]
    ) -> Dict[str, Any]:
        """Generate a human-readable summary of the query results"""
        if not data:
            return {"message": "No data found for the specified criteria"}

        summary = {}

        try:
            if extraction.intent == StockQueryIntent.price:
                if extraction.aggregation:
                    summary["message"] = (
                        f"Price analysis with {extraction.aggregation} aggregation"
                    )
                else:
                    latest_prices = {}
                    for row in data:
                        symbol = row.get("symbol")
                        if symbol and symbol not in latest_prices:
                            latest_prices[symbol] = row.get("close")
                    summary["latest_prices"] = latest_prices
                    summary["message"] = (
                        f"Current prices for {len(latest_prices)} symbols"
                    )

            elif extraction.intent == StockQueryIntent.comparison:
                symbols = list(
                    set(row.get("symbol") for row in data if row.get("symbol"))
                )
                summary["symbols_compared"] = symbols
                summary["message"] = f"Comparison data for {len(symbols)} symbols"

                # Add latest values for comparison
                latest_by_symbol = {}
                for row in data:
                    symbol = row.get("symbol")
                    if symbol and symbol not in latest_by_symbol:
                        latest_by_symbol[symbol] = {
                            k: v for k, v in row.items() if k != "id"
                        }
                summary["latest_values"] = latest_by_symbol

            elif extraction.intent == StockQueryIntent.volatility:
                if data and "volatility" in data[0]:
                    volatilities = [
                        row.get("volatility") for row in data if row.get("volatility")
                    ]
                    if volatilities:
                        avg_volatility = sum(volatilities) / len(volatilities)
                        summary["average_volatility"] = round(avg_volatility, 4)
                        summary["message"] = f"Average volatility: {avg_volatility:.4f}"

            elif extraction.intent == StockQueryIntent.technical:
                summary["message"] = (
                    f"Technical indicators for {len(set(row.get('symbol') for row in data))} symbols"
                )
                if data:
                    # Show latest technical values
                    latest_technical = {}
                    for row in data:
                        symbol = row.get("symbol")
                        if symbol and symbol not in latest_technical:
                            technical_data = {}
                            for metric in ["ma5", "ma10", "ma20", "rsi", "atr"]:
                                if metric in row and row[metric] is not None:
                                    technical_data[metric] = row[metric]
                            latest_technical[symbol] = technical_data
                    summary["technical_indicators"] = latest_technical

            elif extraction.intent == StockQueryIntent.volume:
                if extraction.aggregation and "avg_volume" in data[0]:
                    summary["message"] = "Volume analysis with aggregation"
                else:
                    volumes = [row.get("volume") for row in data if row.get("volume")]
                    if volumes:
                        avg_volume = sum(volumes) / len(volumes)
                        summary["average_volume"] = int(avg_volume)
                        summary["message"] = f"Average volume: {avg_volume:,.0f}"

            else:
                summary["message"] = f"Retrieved {len(data)} records"

            # Add time range info
            if extraction.time_range:
                summary["time_range"] = extraction.time_range

        except Exception as e:
            logger.warning(f"Error generating summary: {str(e)}")
            summary["message"] = data

        return summary

    def query_market_data_hybrid(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to get the stock name or symbol from the query,
        then query the SQLite database for that symbol.
        and return the results.
        """

        try:
            extracted_query = self.extract_symbol_from_query(query)
            if extracted_query and extracted_query.symbols:
                extracted_data = self.execute_dynamic_query(extracted_query)
                try:
                    del extracted_data['sql_query']  # Remove SQL query from output
                except KeyError:    
                    pass  # Handle case where sql_query key doesn't exist
                return extracted_data
            else:
                return []

        except Exception as e:
            logger.error(f"Error in hybrid market data query: {str(e)}")
            return {
                "query": query,
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }

    def extract_symbol_from_query(self, query: str) -> StockQueryExtraction:
        """Extract stock symbols from query using structured output."""

        # Initialize the parser
        parser = PydanticOutputParser(pydantic_object=StockQueryExtraction)

        current_datetime = datetime.now().isoformat()

        # Create the prompt template
        prompt_template = PromptTemplate(
            template="""
            You are a financial data expert. Analyze the following query and extract structured information about stock/crypto data requests.

            Available symbols in database: AAPL, MSFT, JPM, BTC, ETH

            Company mappings:
            - Apple, Apple Inc, AAPL -> AAPL
            - Microsoft, Microsoft Corporation, MSFT -> MSFT  
            - JPMorgan, JP Morgan, JPMorgan Chase, JPM -> JPM
            - Bitcoin, BTC -> BTC
            - Ethereum, ETH -> ETH

            Available metrics in database:
            - Price data: open, high, low, close
            - Volume data: volume
            - Technical indicators: ma5, ma10, ma20, rsi, atr, volatility
            - Change data: pct_change

            Time range keywords:
            - Today current date time : {current_datetime}
            Time range should be always in : ISO FORMAT (YYYY-MM-DD)

            
            Query intents:
            - price: Current/historical prices
            - trend: Price trends and patterns  
            - comparison: Comparing multiple stocks
            - volume: Trading volume analysis
            - volatility: Price volatility analysis
            - technical: Technical indicators (MA, RSI, ATR)
            - change: Price changes and percentages
            - other: General queries

            Aggregation types: avg, max, min, sum, count


            Query: "{query}"

            {format_instructions}

            Rules:
            1. symbols: Extract only valid symbols (AAPL, MSFT, JPM, BTC, ETH). Return empty array if none found.
            2. intent: Classify the query intent from the available options. Use "other" if unclear.
            3. time_range: Extract time period if mentioned, or null if not specified.
            4. metrics: Extract specific data columns requested (close, rsi, ma5, volume, etc.). Use null if not specific.
            5. aggregation: Extract if user wants avg/max/min/etc. Use null if not mentioned.

            Examples:

            "What is the current price of Apple?"
            {{"symbols": ["AAPL"], "intent": "price", "time_range": "today", "metrics": ["close"], "aggregation": null}}

            "Compare Apple and Microsoft's RSI over the last week"
            {{"symbols": ["AAPL", "MSFT"], "intent": "comparison", "time_range": "last week", "metrics": ["rsi"], "aggregation": null}}

            "How volatile has Bitcoin been this month?"
            {{"symbols": ["BTC"], "intent": "volatility", "time_range": "this month", "metrics": ["volatility"], "aggregation": null}}

            "Show 5-day moving average of Apple"
            {{"symbols": ["AAPL"], "intent": "technical", "time_range": null, "metrics": ["ma5"], "aggregation": null}}

            "Average volume of Ethereum yesterday"
            {{"symbols": ["ETH"], "intent": "volume", "time_range": "yesterday", "metrics": ["volume"], "aggregation": "avg"}}

            "Apple and Microsoft performance"
            {{"symbols": ["AAPL", "MSFT"], "intent": "trend", "time_range": null, "metrics": null, "aggregation": null}}

            "Maximum price of JPMorgan last month"
            {{"symbols": ["JPM"], "intent": "price", "time_range": "last month", "metrics": ["high"], "aggregation": "max"}}

            "Weather forecast"
            {{"symbols": [], "intent": "other", "time_range": null, "metrics": null, "aggregation": null}}


            Response:""",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # Create the chain
        chain = prompt_template | self.llm | parser

        try:
            result = chain.invoke({"query": query, "current_datetime": current_datetime})
            return result
        except Exception as e:
            print(f"Error extracting symbols: {e}")
            return []

    def query_market_data_with_ai(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Query market data using natural language with LangChain SQL agent

        Args:
            natural_language_query: Natural language query about market data

        Returns:
            Dictionary containing query results and analysis
        """
        try:
            if not self.sql_agent:
                logger.warning("SQL agent not available, falling back to basic query")
                return self._fallback_query(natural_language_query)

            # Enhanced prompt for financial context
            enhanced_query = f"""
            You are a financial data analyst. Answer the following question about stock market data.
            
            Database Schema:
            - Table: stock_data
            - Columns: id, symbol, timestamp, open, high, low, close, volume, ma5, ma10, ma20, rsi, volatility, atr, pct_change
            - symbol: Stock/crypto symbols (AAPL, MSFT, JPM, BTC, ETH)
            - Technical indicators: ma5/ma10/ma20 (moving averages), rsi (0-100), atr (average true range)
            - Financial metrics: open/high/low/close prices, volume, pct_change (percentage change)
            
            Question: {natural_language_query}
            
            Please provide SQL query results and interpret them in financial context.
            If asking about trends, compare multiple time periods.
            If asking about technical analysis, explain the indicators.
            Provide results in short brief.
            """

            # Execute query with agent
            response = self.sql_agent.invoke({"input": enhanced_query})

            # Parse and format response
            result = {
                "query": natural_language_query,
                "ai_response": (
                    response.get("output", "")
                    if isinstance(response, dict)
                    else str(response)
                ),
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Successfully processed AI query: '{natural_language_query}'")
            return result

        except Exception as e:
            logger.error(f"Error in AI query: {str(e)}")
            return {
                "query": natural_language_query,
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }

    def _fallback_query(self, query: str) -> Dict[str, Any]:
        """Fallback query method when SQL agent is not available"""
        try:
            # Simple keyword-based fallback
            query_lower = query.lower()

            if "latest" in query_lower or "current" in query_lower:
                return {"data": self.get_latest_market_data(), "type": "latest_data"}
            elif "summary" in query_lower:
                return {"data": self.get_market_summary(), "type": "summary"}
            elif any(
                symbol in query_lower
                for symbol in ["aapl", "msft", "jpm", "btc", "eth"]
            ):
                # Extract symbol and get its data
                for symbol in ["AAPL", "MSFT", "JPM", "BTC", "ETH"]:
                    if symbol.lower() in query_lower:
                        return {
                            "data": self.get_symbol_history(symbol),
                            "type": "symbol_history",
                        }

            return {"error": "Could not process query", "status": "error"}

        except Exception as e:
            return {"error": str(e), "status": "error"}

    def get_market_insights(self, symbol: str = None) -> Dict[str, Any]:
        """Get AI-generated market insights for specific symbol or overall market"""
        try:
            if symbol:
                query = f"Analyze the latest technical indicators and price trends for {symbol}. What do the RSI, moving averages, and recent price action suggest?"
            else:
                query = "Provide an overall market analysis comparing the performance and technical indicators across all available symbols."

            return self.query_market_data_with_ai(query)

        except Exception as e:
            logger.error(f"Error generating market insights: {str(e)}")
            return {"error": str(e), "status": "error"}

    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def query_market_data(
        self,
        query: str = None,
        symbols: Optional[List[str]] = None,
        limit: int = 10,
        latest_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Traditional SQL query method (kept for backward compatibility)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.cursor()

                # Build SQL query
                if latest_only:
                    sql_query = """
                        SELECT * FROM (
                            SELECT *, ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
                            FROM stock_data
                            WHERE 1=1
                    """
                    params = []
                else:
                    sql_query = """
                        SELECT * FROM stock_data 
                        WHERE 1=1
                    """
                    params = []

                # Add query filter
                if query:
                    sql_query += " AND symbol LIKE ?"
                    params.append(f"%{query}%")

                # Add symbol filter if provided
                if symbols:
                    placeholders = ",".join(["?" for _ in symbols])
                    sql_query += f" AND symbol IN ({placeholders})"
                    params.extend(symbols)

                if latest_only:
                    sql_query += ") WHERE rn = 1"

                sql_query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor.execute(sql_query, params)
                results = cursor.fetchall()

                # Convert to list of dictionaries
                market_records = [dict(row) for row in results]

                logger.info(f"Retrieved {len(market_records)} market data records")
                return market_records

        except Exception as e:
            logger.error(f"Error querying market data: {str(e)}")
            return []

    def get_latest_market_data(
        self, symbols: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get the latest market data for specified symbols"""
        return self.query_market_data(symbols=symbols, latest_only=True, limit=50)

    def get_symbol_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical data for a specific symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM stock_data 
                    WHERE symbol = ? 
                    AND timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                """.format(
                        days
                    ),
                    (symbol,),
                )

                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting symbol history: {str(e)}")
            return []

    def get_market_summary(self) -> Dict[str, Any]:
        """Get summary statistics of stored market data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get total records
                cursor.execute("SELECT COUNT(*) as total_records FROM stock_data")
                total_records = cursor.fetchone()[0]

                # Get unique symbols
                cursor.execute(
                    "SELECT COUNT(DISTINCT symbol) as unique_symbols FROM stock_data"
                )
                unique_symbols = cursor.fetchone()[0]

                # Get latest update time
                cursor.execute(
                    "SELECT MAX(updated_at) as latest_update FROM stock_data"
                )
                latest_update = cursor.fetchone()[0]

                # Get symbols with record counts
                cursor.execute(
                    """
                    SELECT symbol, COUNT(*) as record_count, MAX(timestamp) as latest_data
                    FROM stock_data 
                    GROUP BY symbol 
                    ORDER BY record_count DESC
                """
                )
                symbol_stats = [
                    {"symbol": row[0], "records": row[1], "latest_data": row[2]}
                    for row in cursor.fetchall()
                ]

                return {
                    "total_records": total_records,
                    "unique_symbols": unique_symbols,
                    "latest_update": latest_update,
                    "symbol_statistics": symbol_stats,
                }

        except Exception as e:
            logger.error(f"Error getting market summary: {str(e)}")
            return {}

    def clear_old_data(self, days_to_keep: int = 30):
        """Remove market data older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM stock_data 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(
                        days_to_keep
                    )
                )

                deleted_rows = cursor.rowcount
                conn.commit()

                logger.info(f"Cleaned up {deleted_rows} old stock data records")
                return deleted_rows

        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            return 0
