from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating  import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from memory.conv_memory import init_db
from contextlib import asynccontextmanager

def init_app():
    app = FastAPI()
    

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development; restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Startup event to initialize the database
    @asynccontextmanager
    async def lifespan():
        """
        Initialize the database connection when the application starts.
        """
        init_db()

    # Serve static files from the 'static' directory
    app.mount("/static", StaticFiles(directory="./static"), name="static")

    # Serve templates using Jinja2
    templates = Jinja2Templates(directory="./templates/")
   
    # render index.html
    @app.get("/",response_class=HTMLResponse)
    async def index(request:Request):
        return templates.TemplateResponse("index.html",context={"request":request})

    
    # Health
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint to verify the server is running.
        """
        return {"status": "ok"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    # Note: In production, use a proper ASGI server like Gunicorn or Daphne