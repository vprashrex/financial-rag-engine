"""
This script is used to test the sql agent for market data retrieval.
"""

from core.stock_market.market_engine import MarketEngine
import os
def main():
    market_engine = MarketEngine()

    # TODO: Uncomment the line below to fetch and update market data before querying
    #market_engine.fetch_and_update_market_data()  # Fetch and update market data
    
    if not os.path.exists(""):
        print(f"Market data file {market_engine.market_data_file} does not exist. Please fetch market data first.")
        return

    while True:
        query = input("Enter your query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        results = market_engine.query_market_data_hybrid(query)  # Query market data with AI
        print(results)  # Print the results of the query

"""
Example usage:
--------------------- EXAMPLE 1 ---------------------
INPUT: stock price comparision of microsoft and apple
OUTPUT: {'symbols_compared': ['AAPL', 'MSFT'], 'message': 'Comparison data for 2 symbols', 'latest_values': {'MSFT': {'symbol': 'MSFT', 'timestamp': '2025-06-05T00:00:00', 'close': 467.68}, 'AAPL': {'symbol': 'AAPL', 'timestamp': '2025-06-05T00:00:00', 'close': 200.63}}}

--------------------- EXAMPLE 2 ---------------------
INPUT: trend of JPM
OUTPUT: {'status': 'success', 'query_info': {'symbols': ['JPM'], 'intent': 'trend', 'time_range': None, 'metrics': None, 'aggregation': None}, 'sql_query': 'SELECT symbol, timestamp, close, ma5, ma20, pct_change FROM stock_data WHERE symbol IN (?) ORDER BY timestamp DESC LIMIT 10', 'record_count': 10, 'data': [{'symbol': 'JPM', 'timestamp': '2025-06-05T00:00:00', 'close': 261.95, 'ma5': 264.22, 'ma20': 262.87649999999996, 'pct_change': -0.859132541064278}, {'symbol': 'JPM', 'timestamp': '2025-06-04T00:00:00', 'close': 264.22, 'ma5': 264.704, 'ma20': 262.24850000000004, 'pct_change': -0.76989521913845}, {'symbol': 'JPM', 'timestamp': '2025-06-03T00:00:00', 'close': 266.27, 'ma5': 264.558, 'ma20': 261.5, 'pct_change': 0.6083276656842607}, {'symbol': 'JPM', 'timestamp': '2025-06-02T00:00:00', 'close': 264.66, 'ma5': 264.36199999999997, 'ma20': 260.8145, 'pct_change': 0.2500000000000169}, {'symbol': 'JPM', 'timestamp': '2025-05-30T00:00:00', 'close': 264.0, 'ma5': 263.572, 'ma20': 260.207, 'pct_change': -0.13995536558610855}, {'symbol': 'JPM', 'timestamp': '2025-05-29T00:00:00', 'close': 264.37, 'ma5': 262.90600000000006, 'ma20': 259.35150000000004, 'pct_change': 0.33397851910887955}, {'symbol': 'JPM', 'timestamp': '2025-05-28T00:00:00', 'close': 263.49, 'ma5': 262.24, 'ma20': 258.36400000000003, 'pct_change': -0.67850277055298}, {'symbol': 'JPM', 'timestamp': '2025-05-27T00:00:00', 'close': 265.29, 'ma5': 262.678, 'ma20': 257.4205, 'pct_change': 1.7567412067047927}, {'symbol': 'JPM', 'timestamp': '2025-05-23T00:00:00', 'close': 260.71, 'ma5': 262.596, 'ma20': 256.317, 'pct_change': 0.015345072313643904}, {'symbol': 'JPM', 'timestamp': '2025-05-22T00:00:00', 'close': 260.67, 'ma5': 263.966, 'ma20': 255.45899999999997, 'pct_change': -0.1417407293901385}], 'summary': {'message': 'Retrieved 10 records'}, 'timestamp': '2025-06-06T15:16:17.805496'}

---------------------- EXAMPLE 3 ---------------------
INPUT: stock price of microsoft at 2025-06-05
OUTPUT: {'latest_prices': {'MSFT': 467.68}, 'message': 'Current prices for 1 symbols', 'time_range': '2025-06-05'}
{'status': 'success', 'query_info': {'symbols': ['MSFT'], 'intent': 'price', 'time_range': '2025-06-05', 'metrics': ['close'], 'aggregation': None}, 'sql_query': 'SELECT symbol, timestamp, close FROM stock_data WHERE symbol IN (?) ORDER BY timestamp DESC LIMIT 10', 'record_count': 10, 'data': [{'symbol': 'MSFT', 'timestamp': '2025-06-05T00:00:00', 'close': 467.68}, {'symbol': 'MSFT', 'timestamp': '2025-06-04T00:00:00', 'close': 463.87}, {'symbol': 'MSFT', 'timestamp': '2025-06-03T00:00:00', 'close': 462.97}, {'symbol': 'MSFT', 'timestamp': '2025-06-02T00:00:00', 'close': 461.97}, {'symbol': 'MSFT', 'timestamp': '2025-05-30T00:00:00', 'close': 460.36}, {'symbol': 'MSFT', 'timestamp': '2025-05-29T00:00:00', 'close': 458.68}, {'symbol': 'MSFT', 'timestamp': '2025-05-28T00:00:00', 'close': 457.36}, {'symbol': 'MSFT', 'timestamp': '2025-05-27T00:00:00', 'close': 460.69}, {'symbol': 'MSFT', 'timestamp': '2025-05-23T00:00:00', 'close': 450.18}, {'symbol': 'MSFT', 'timestamp': '2025-05-22T00:00:00', 'close': 454.86}], 'summary': {'latest_prices': {'MSFT': 467.68}, 'message': 'Current prices for 1 symbols', 'time_range': '2025-06-05'}, 'timestamp': '2025-06-06T15:17:23.132174'}

---------------------- EXAMPLE 4 ---------------------
INPUT: stock price of ola at 2025-06-05
OUTPUT: []

---------------------- EXAMPLE 5 ---------------------
INPUT: stock price of jp morgan previous 7 day
OUTPUT: {'status': 'success', 'query_info': {'symbols': ['JPM'], 'intent': 'price', 'time_range': 'previous 7 day', 'metrics': ['close'], 'aggregation': None}, 'record_count': 50, 'data': [{'symbol': 'JPM', 'timestamp': '2025-06-05T00:00:00', 'close': 261.95}, {'symbol': 'JPM', 'timestamp': '2025-06-04T00:00:00', 'close': 264.22}, {'symbol': 'JPM', 'timestamp': '2025-06-03T00:00:00', 'close': 266.27}, {'symbol': 'JPM', 'timestamp': '2025-06-02T00:00:00', 'close': 264.66}, {'symbol': 'JPM', 'timestamp': '2025-05-30T00:00:00', 'close': 264.0}, {'symbol': 'JPM', 'timestamp': '2025-05-29T00:00:00', 'close': 264.37}, {'symbol': 'JPM', 'timestamp': '2025-05-28T00:00:00', 'close': 263.49}, {'symbol': 'JPM', 'timestamp': '2025-05-27T00:00:00', 'close': 265.29}, {'symbol': 'JPM', 'timestamp': '2025-05-23T00:00:00', 'close': 260.71}, {'symbol': 'JPM', 'timestamp': '2025-05-22T00:00:00', 'close': 260.67}, {'symbol': 'JPM', 'timestamp': '2025-05-21T00:00:00', 'close': 261.04}, {'symbol': 'JPM', 'timestamp': '2025-05-20T00:00:00', 'close': 265.68}, {'symbol': 'JPM', 'timestamp': '2025-05-19T00:00:00', 'close': 264.88}, {'symbol': 'JPM', 'timestamp': '2025-05-16T00:00:00', 'close': 267.56}, {'symbol': 'JPM', 'timestamp': '2025-05-15T00:00:00', 'close': 267.49}, {'symbol': 'JPM', 'timestamp': '2025-05-14T00:00:00', 'close': 265.64}, {'symbol': 'JPM', 'timestamp': '2025-05-13T00:00:00', 'close': 263.01}, {'symbol': 'JPM', 'timestamp': '2025-05-12T00:00:00', 'close': 260.05}, {'symbol': 'JPM', 'timestamp': '2025-05-09T00:00:00', 'close': 253.08}, {'symbol': 'JPM', 'timestamp': '2025-05-08T00:00:00', 'close': 253.47}, {'symbol': 'JPM', 'timestamp': '2025-05-07T00:00:00', 'close': 249.39}, {'symbol': 'JPM', 'timestamp': '2025-05-06T00:00:00', 'close': 249.25}, {'symbol': 'JPM', 'timestamp': '2025-05-05T00:00:00', 'close': 252.56}, {'symbol': 'JPM', 'timestamp': '2025-05-02T00:00:00', 'close': 252.51}, {'symbol': 'JPM', 'timestamp': '2025-05-01T00:00:00', 'close': 246.89}, {'symbol': 'JPM', 'timestamp': '2025-04-30T00:00:00', 'close': 244.62}, {'symbol': 'JPM', 'timestamp': '2025-04-29T00:00:00', 'close': 244.62}, {'symbol': 'JPM', 'timestamp': '2025-04-28T00:00:00', 'close': 243.22}, {'symbol': 'JPM', 'timestamp': '2025-04-25T00:00:00', 'close': 243.55}, {'symbol': 'JPM', 'timestamp': '2025-04-24T00:00:00', 'close': 244.64}, {'symbol': 'JPM', 'timestamp': '2025-04-23T00:00:00', 'close': 240.88}, {'symbol': 'JPM', 'timestamp': '2025-04-22T00:00:00', 'close': 235.59}, {'symbol': 'JPM', 'timestamp': '2025-04-21T00:00:00', 'close': 228.99}, {'symbol': 'JPM', 'timestamp': '2025-04-17T00:00:00', 'close': 231.96}, {'symbol': 'JPM', 'timestamp': '2025-04-16T00:00:00', 'close': 229.61}, {'symbol': 'JPM', 'timestamp': '2025-04-15T00:00:00', 'close': 233.13}, {'symbol': 'JPM', 'timestamp': '2025-04-14T00:00:00', 'close': 234.72}, {'symbol': 'JPM', 'timestamp': '2025-04-11T00:00:00', 'close': 236.2}, {'symbol': 'JPM', 'timestamp': '2025-04-10T00:00:00', 'close': 227.11}, {'symbol': 'JPM', 'timestamp': '2025-04-09T00:00:00', 'close': 234.34}, {'symbol': 'JPM', 'timestamp': '2025-04-08T00:00:00', 'close': 216.87}, {'symbol': 'JPM', 'timestamp': '2025-04-07T00:00:00', 'close': 214.44}, {'symbol': 'JPM', 'timestamp': '2025-04-04T00:00:00', 'close': 210.28}, {'symbol': 'JPM', 'timestamp': '2025-04-03T00:00:00', 'close': 228.69}, {'symbol': 'JPM', 'timestamp': '2025-04-02T00:00:00', 'close': 245.82}, {'symbol': 'JPM', 'timestamp': '2025-04-01T00:00:00', 'close': 243.66}, {'symbol': 'JPM', 'timestamp': '2025-03-31T00:00:00', 'close': 245.3}, {'symbol': 'JPM', 'timestamp': '2025-03-28T00:00:00', 'close': 242.85}, {'symbol': 'JPM', 'timestamp': '2025-03-27T00:00:00', 'close': 248.12}, {'symbol': 'JPM', 'timestamp': '2025-03-26T00:00:00', 'close': 251.03}], 'summary': {'latest_prices': {'JPM': 261.95}, 'message': 'Current prices for 1 symbols', 'time_range': 'previous 7 day'}, 'timestamp': '2025-06-06T15:33:02.922938'}
"""


if __name__ == "__main__":
    main()