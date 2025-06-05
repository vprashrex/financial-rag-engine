import logging
import os
from datetime import datetime

def setup_logger(name):
    log_directory = os.path.join("logs", name)
    os.makedirs(log_directory, exist_ok=True)
    
    log_filename = os.path.join(log_directory, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log")
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
        
    return logger

vector_logger = setup_logger("vector")
llm_logger = setup_logger("llm")
api_logger = setup_logger("apiServer")
stock_logger = setup_logger("stock")    