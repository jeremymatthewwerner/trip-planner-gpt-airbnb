from api.main import app

# This file is just a wrapper to make deployment easier
# The actual application is defined in api/main.py
# 
# Important endpoints:
# - /airbnb/search - Search for Airbnb listings
# - /airbnb/listings/images - Get Airbnb listings with images
# - /debug/info - Get information about the server environment
# - /debug/files - Check the file system on the server

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 