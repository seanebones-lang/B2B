"""Main FastAPI application entry point"""

import uvicorn
from api.rest import app

if __name__ == "__main__":
    uvicorn.run(
        "api.rest:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
