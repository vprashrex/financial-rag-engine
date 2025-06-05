from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def init_app():
    app = FastAPI()

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development; restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include the stock market API router
    from api.stock_market.stock_market_api import router as stock_market_router
    app.include_router(stock_market_router, prefix="/api/stock_market", tags=["Stock Market"])

    # Include the document upload API router
    from api.document_upload.upload_api import router as upload_router
    app.include_router(upload_router, prefix="/api/document_upload", tags=["Document Upload"])

    # Include the chat API router
    from api.chat.chat_api import router as chat_router
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])

    return app

app = init_app()