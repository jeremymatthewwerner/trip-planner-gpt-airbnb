from api.main import app

# This file is just a wrapper to make deployment easier
# The actual application is defined in api/main.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 