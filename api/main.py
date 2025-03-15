from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import json
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trip Planner API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Get RapidAPI key from environment variables
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    logger.warning("RAPIDAPI_KEY not set. Will fall back to mock data.")

# Models
class AirbnbListingRequest(BaseModel):
    location: str
    check_in: str
    check_out: str
    adults: int
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    room_type: Optional[str] = None

class AirbnbListing(BaseModel):
    id: str
    name: str
    url: str
    image_url: str
    price_per_night: float
    total_price: float
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    room_type: str
    beds: int
    bedrooms: int
    bathrooms: float
    amenities: List[str]
    location: str
    superhost: bool

class AttractionRequest(BaseModel):
    location: str
    category: Optional[str] = None
    budget: Optional[str] = None

class Attraction(BaseModel):
    name: str
    description: str
    category: str
    price_level: str
    rating: float
    reviews_count: int
    url: str
    image_url: Optional[str] = None
    location: str

class ItineraryRequest(BaseModel):
    location: str
    start_date: str
    end_date: str
    interests: Optional[List[str]] = None
    pace: Optional[str] = None

class ItineraryDay(BaseModel):
    date: str
    activities: List[dict]

class Itinerary(BaseModel):
    location: str
    days: List[ItineraryDay]

# Mock data for development (in a real app, this would come from actual API calls)
def load_mock_data(filename):
    try:
        with open(f"api/mock_data/{filename}", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Create directory if it doesn't exist
        os.makedirs("api/mock_data", exist_ok=True)
        # Return empty data
        return []

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the Trip Planner API"}

@app.head("/")
async def root_head():
    return JSONResponse(content={}, status_code=200)

@app.post("/airbnb/search", response_model=List[AirbnbListing])
async def search_airbnb_listings(request: AirbnbListingRequest):
    """
    Search for Airbnb listings based on location, dates, and other criteria.
    Uses RapidAPI if API key is available, otherwise falls back to mock data.
    """
    logger.info(f"Searching Airbnb listings for {request.location}")
    
    try:
        # Try to use RapidAPI if key is available
        if RAPIDAPI_KEY:
            return await search_airbnb_rapidapi(request)
        else:
            logger.info("No RapidAPI key found. Using mock data.")
            return search_airbnb_mock(request)
    
    except Exception as e:
        logger.error(f"Error searching Airbnb listings: {str(e)}")
        # Fall back to mock data if RapidAPI fails
        if str(e).startswith("RapidAPI error"):
            logger.info("RapidAPI failed. Falling back to mock data.")
            return search_airbnb_mock(request)
        raise HTTPException(status_code=500, detail=f"Error searching Airbnb listings: {str(e)}")

async def search_airbnb_rapidapi(request: AirbnbListingRequest):
    """
    Search for Airbnb listings using RapidAPI.
    """
    logger.info(f"Using RapidAPI to search for Airbnb listings in {request.location}")
    
    # Using ApiDojo's Airbnb API on RapidAPI
    url = "https://airbnb13.p.rapidapi.com/search-location"
    
    # Convert room_type to the format expected by the API
    room_type_map = {
        "entire_home": "entire_home_apt",
        "private_room": "private_room",
        "shared_room": "shared_room",
        "hotel_room": "hotel_room"
    }
    
    # Prepare query parameters
    query_params = {
        "location": request.location,
        "checkin": request.check_in,
        "checkout": request.check_out,
        "adults": request.adults,
        "children": 0,
        "infants": 0,
        "pets": 0,
        "page": 1,
        "currency": "USD"
    }
    
    # Add optional parameters if provided
    if request.price_min is not None:
        query_params["price_min"] = request.price_min
    if request.price_max is not None:
        query_params["price_max"] = request.price_max
    if request.room_type and request.room_type in room_type_map:
        query_params["room_type"] = room_type_map[request.room_type]
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "airbnb13.p.rapidapi.com"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=query_params, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"RapidAPI error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Transform the API response to match our data model
        listings = []
        for item in data.get("results", []):
            try:
                listing = {
                    "id": str(item.get("id", "")),
                    "name": item.get("name", ""),
                    "url": f"https://www.airbnb.com/rooms/{item.get('id', '')}",
                    "image_url": item.get("images", [{}])[0].get("picture", "") if item.get("images") else "",
                    "price_per_night": float(item.get("price", {}).get("rate", 0)),
                    "total_price": float(item.get("price", {}).get("total", 0)),
                    "rating": float(item.get("rating", 0)),
                    "reviews_count": int(item.get("reviewsCount", 0)),
                    "room_type": item.get("type", ""),
                    "beds": int(item.get("beds", 1)),
                    "bedrooms": int(item.get("bedrooms", 1)),
                    "bathrooms": float(item.get("bathrooms", 1.0)),
                    "amenities": item.get("previewAmenities", []),
                    "location": request.location,
                    "superhost": bool(item.get("isSuperhost", False))
                }
                listings.append(listing)
            except Exception as e:
                logger.error(f"Error processing listing: {str(e)}")
                continue
        
        return listings

def search_airbnb_mock(request: AirbnbListingRequest):
    """
    Search for Airbnb listings using mock data.
    """
    logger.info(f"Using mock data for Airbnb listings in {request.location}")
    
    # Load mock data
    mock_listings = load_mock_data("airbnb_listings.json")
    
    # If mock data is empty, create some sample data
    if not mock_listings:
        mock_listings = [
            {
                "id": "12345",
                "name": "Luxury Beachfront Villa",
                "url": "https://www.airbnb.com/rooms/12345",
                "image_url": "https://example.com/image1.jpg",
                "price_per_night": 250.0,
                "total_price": 1750.0,
                "rating": 4.9,
                "reviews_count": 120,
                "room_type": "entire_home",
                "beds": 3,
                "bedrooms": 2,
                "bathrooms": 2.5,
                "amenities": ["Pool", "Wifi", "Kitchen", "Air conditioning"],
                "location": request.location,
                "superhost": True
            },
            {
                "id": "67890",
                "name": "Cozy Downtown Apartment",
                "url": "https://www.airbnb.com/rooms/67890",
                "image_url": "https://example.com/image2.jpg",
                "price_per_night": 120.0,
                "total_price": 840.0,
                "rating": 4.7,
                "reviews_count": 85,
                "room_type": "entire_home",
                "beds": 1,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Wifi", "Kitchen", "Air conditioning"],
                "location": request.location,
                "superhost": False
            },
            {
                "id": "24680",
                "name": "Private Room in Historic Home",
                "url": "https://www.airbnb.com/rooms/24680",
                "image_url": "https://example.com/image3.jpg",
                "price_per_night": 75.0,
                "total_price": 525.0,
                "rating": 4.8,
                "reviews_count": 65,
                "room_type": "private_room",
                "beds": 1,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Wifi", "Shared kitchen", "Garden"],
                "location": request.location,
                "superhost": True
            }
        ]
        
        # Save mock data for future use
        os.makedirs("api/mock_data", exist_ok=True)
        with open("api/mock_data/airbnb_listings.json", "w") as f:
            json.dump(mock_listings, f)
    
    # Filter by room type if specified
    if request.room_type:
        mock_listings = [listing for listing in mock_listings if listing["room_type"] == request.room_type]
    
    # Filter by price range if specified
    if request.price_min is not None:
        mock_listings = [listing for listing in mock_listings if listing["price_per_night"] >= request.price_min]
    if request.price_max is not None:
        mock_listings = [listing for listing in mock_listings if listing["price_per_night"] <= request.price_max]
    
    return mock_listings

@app.post("/attractions/search", response_model=List[Attraction])
async def search_attractions(request: AttractionRequest):
    """
    Search for attractions and activities at a destination.
    In a production environment, this would call a travel API.
    """
    logger.info(f"Searching attractions in {request.location}")
    
    try:
        # In a real implementation, this would call a travel API
        # For now, we'll use mock data
        mock_attractions = load_mock_data("attractions.json")
        
        # If mock data is empty, create some sample data
        if not mock_attractions:
            mock_attractions = [
                {
                    "name": "Central Park",
                    "description": "Iconic urban park with walking paths, a zoo, and boat rentals.",
                    "category": "outdoor",
                    "price_level": "low",
                    "rating": 4.8,
                    "reviews_count": 1200,
                    "url": "https://www.centralparknyc.org/",
                    "image_url": "https://example.com/central_park.jpg",
                    "location": request.location
                },
                {
                    "name": "Metropolitan Museum of Art",
                    "description": "One of the world's largest and finest art museums.",
                    "category": "museums",
                    "price_level": "medium",
                    "rating": 4.9,
                    "reviews_count": 950,
                    "url": "https://www.metmuseum.org/",
                    "image_url": "https://example.com/met.jpg",
                    "location": request.location
                },
                {
                    "name": "Le Bernardin",
                    "description": "Upscale French seafood restaurant with prix fixe menus.",
                    "category": "food",
                    "price_level": "high",
                    "rating": 4.7,
                    "reviews_count": 780,
                    "url": "https://www.le-bernardin.com/",
                    "image_url": "https://example.com/le_bernardin.jpg",
                    "location": request.location
                }
            ]
            
            # Save mock data for future use
            os.makedirs("api/mock_data", exist_ok=True)
            with open("api/mock_data/attractions.json", "w") as f:
                json.dump(mock_attractions, f)
        
        # Filter by category if specified
        if request.category:
            mock_attractions = [attraction for attraction in mock_attractions if attraction["category"] == request.category]
        
        # Filter by budget if specified
        if request.budget:
            mock_attractions = [attraction for attraction in mock_attractions if attraction["price_level"] == request.budget]
        
        return mock_attractions
    
    except Exception as e:
        logger.error(f"Error searching attractions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching attractions: {str(e)}")

@app.post("/itinerary/create", response_model=Itinerary)
async def create_itinerary(request: ItineraryRequest):
    """
    Create a daily itinerary for the trip.
    In a production environment, this would use more sophisticated logic.
    """
    logger.info(f"Creating itinerary for {request.location} from {request.start_date} to {request.end_date}")
    
    try:
        # Parse dates
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        # Calculate number of days
        delta = end_date - start_date
        num_days = delta.days + 1
        
        # Get attractions for the location
        attractions = await search_attractions(AttractionRequest(location=request.location))
        
        # Create itinerary days
        days = []
        for i in range(num_days):
            current_date = start_date.replace(day=start_date.day + i)
            formatted_date = current_date.strftime("%Y-%m-%d")
            
            # Simple logic to assign attractions to days
            # In a real app, this would be more sophisticated
            day_attractions = []
            for j, attraction in enumerate(attractions):
                if j % num_days == i:
                    day_attractions.append({
                        "time": "10:00 AM" if j == 0 else ("2:00 PM" if j == 1 else "7:00 PM"),
                        "name": attraction["name"],
                        "description": attraction["description"],
                        "category": attraction["category"],
                        "price_level": attraction["price_level"]
                    })
            
            days.append({
                "date": formatted_date,
                "activities": day_attractions
            })
        
        return {
            "location": request.location,
            "days": days
        }
    
    except Exception as e:
        logger.error(f"Error creating itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating itinerary: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 