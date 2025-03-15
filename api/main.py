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
        # Use absolute path to find the mock data
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mock_data_path = os.path.join(base_dir, "api", "mock_data", filename)
        logger.info(f"Loading mock data from: {mock_data_path}")
        
        with open(mock_data_path, "r") as f:
            data = json.load(f)
            logger.info(f"Successfully loaded mock data: {len(data)} items")
            return data
    except FileNotFoundError as e:
        logger.error(f"Mock data file not found: {str(e)}")
        # Create directory if it doesn't exist
        os.makedirs(os.path.join(base_dir, "api", "mock_data"), exist_ok=True)
        # Return empty data
        return []
    except Exception as e:
        logger.error(f"Error loading mock data: {str(e)}")
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
        # Try to use RapidAPI if key is available and not a placeholder
        if RAPIDAPI_KEY and RAPIDAPI_KEY != "your_valid_rapidapi_key_here":
            try:
                return await search_airbnb_rapidapi(request)
            except Exception as api_error:
                logger.error(f"RapidAPI search failed: {str(api_error)}")
                logger.info("Falling back to mock data.")
                return search_airbnb_mock(request)
        else:
            logger.info("No valid RapidAPI key found. Using mock data.")
            return search_airbnb_mock(request)
    
    except Exception as e:
        logger.error(f"Error searching Airbnb listings: {str(e)}")
        # Always try to return mock data as a last resort
        try:
            return search_airbnb_mock(request)
        except Exception as mock_error:
            logger.error(f"Mock data fallback also failed: {str(mock_error)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve Airbnb listings")

async def search_airbnb_rapidapi(request: AirbnbListingRequest):
    """
    Search for Airbnb listings using RapidAPI.
    Falls back to mock data if the API call fails.
    """
    url = "https://airbnb13.p.rapidapi.com/search-location"
    
    # Map our room types to RapidAPI's room types
    room_type_map = {
        "entire_home": "entire_home",
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
    
    try:
        # Only attempt the API call if we have a RapidAPI key
        if not RAPIDAPI_KEY or RAPIDAPI_KEY == "your_valid_rapidapi_key_here":
            logger.warning("No valid RAPIDAPI_KEY provided. Using mock data.")
            raise Exception("No valid RAPIDAPI_KEY provided")
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=query_params, headers=headers)
            
            if response.status_code != 200:
                error_message = f"RapidAPI error: {response.status_code}"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and "message" in error_data:
                        error_message += f" - {error_data['message']}"
                except:
                    error_message += f" - {response.text}"
                
                logger.error(error_message)
                raise Exception(error_message)
            
            data = response.json()
            
            # Transform the API response to match our data model
            listings = []
            for item in data.get("results", []):
                try:
                    # Make sure item is a dictionary before trying to access its properties
                    if not isinstance(item, dict):
                        logger.error(f"Expected dictionary but got {type(item)}: {item}")
                        continue
                        
                    # Safely extract values with proper type checking
                    item_id = str(item.get("id", "")) if item.get("id") is not None else ""
                    name = item.get("name", "") if isinstance(item.get("name"), str) else ""
                    
                    # Safely handle nested structures
                    images = item.get("images", []) if isinstance(item.get("images"), list) else []
                    image_url = ""
                    if images and isinstance(images[0], dict):
                        image_url = images[0].get("picture", "")
                    
                    # Safely handle price information
                    price = item.get("price", {}) if isinstance(item.get("price"), dict) else {}
                    price_per_night = 0.0
                    total_price = 0.0
                    if isinstance(price, dict):
                        price_per_night = float(price.get("rate", 0)) if price.get("rate") is not None else 0.0
                        total_price = float(price.get("total", 0)) if price.get("total") is not None else 0.0
                    
                    # Create a URL with date and guest parameters using Airbnb's actual URL format
                    # Format: https://www.airbnb.com/rooms/ID?adults=X&check_in=YYYY-MM-DD&check_out=YYYY-MM-DD
                    # Preserve any existing source_impression_id if present in the API response
                    base_url = f"https://www.airbnb.com/rooms/{item_id}"
                    
                    # Check if the API already returned a URL with parameters
                    api_url = item.get("url", "")
                    source_impression_id = ""
                    
                    # Extract source_impression_id from API URL if present
                    if api_url and "source_impression_id=" in api_url:
                        import re
                        match = re.search(r'source_impression_id=([^&]+)', api_url)
                        if match:
                            source_impression_id = match.group(1)
                    
                    # Build the URL with our parameters
                    url_with_params = f"{base_url}?adults={request.adults}&check_in={request.check_in}&check_out={request.check_out}"
                    
                    # Add source_impression_id if we found one
                    if source_impression_id:
                        url_with_params += f"&source_impression_id={source_impression_id}"
                    
                    listing = {
                        "id": item_id,
                        "name": name,
                        "url": url_with_params if item_id else "",
                        "image_url": image_url,
                        "price_per_night": price_per_night,
                        "total_price": total_price,
                        "rating": float(item.get("rating", 0)) if item.get("rating") is not None else 0.0,
                        "reviews_count": int(item.get("reviewsCount", 0)) if item.get("reviewsCount") is not None else 0,
                        "room_type": item.get("type", "") if isinstance(item.get("type"), str) else "",
                        "beds": int(item.get("beds", 1)) if item.get("beds") is not None else 1,
                        "bedrooms": int(item.get("bedrooms", 1)) if item.get("bedrooms") is not None else 1,
                        "bathrooms": float(item.get("bathrooms", 1.0)) if item.get("bathrooms") is not None else 1.0,
                        "amenities": item.get("previewAmenities", []) if isinstance(item.get("previewAmenities"), list) else [],
                        "location": request.location,
                        "superhost": bool(item.get("isSuperhost", False)) if item.get("isSuperhost") is not None else False
                    }
                    listings.append(listing)
                except Exception as e:
                    logger.error(f"Error processing listing: {str(e)}")
                    continue
            
            return listings
    except Exception as e:
        logger.error(f"Error in RapidAPI request: {str(e)}")
        # Fall back to mock data
        return search_airbnb_mock(request)

def search_airbnb_mock(request: AirbnbListingRequest):
    """
    Search for Airbnb listings using mock data.
    """
    logger.info(f"Using mock data for Airbnb listings in {request.location}")
    
    # Load mock data
    mock_listings = load_mock_data("airbnb_listings.json")
    logger.info(f"Loaded {len(mock_listings)} mock listings")
    
    # If mock data is empty, create some sample data
    if not mock_listings:
        logger.info("No mock listings found, creating sample data")
        mock_listings = [
            {
                "id": "12345",
                "name": "Luxury Beachfront Villa",
                "url": f"https://www.airbnb.com/rooms/12345?adults={request.adults}&check_in={request.check_in}&check_out={request.check_out}",
                "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1000&auto=format&fit=crop",
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
                "url": f"https://www.airbnb.com/rooms/67890?adults={request.adults}&check_in={request.check_in}&check_out={request.check_out}",
                "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?q=80&w=1000&auto=format&fit=crop",
                "price_per_night": 120.0,
                "total_price": 840.0,
                "rating": 4.7,
                "reviews_count": 85,
                "room_type": "entire_home",
                "beds": 1,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Wifi", "Kitchen", "Washer"],
                "location": request.location,
                "superhost": False
            },
            {
                "id": "24680",
                "name": "Mountain Retreat Cabin",
                "url": f"https://www.airbnb.com/rooms/24680?adults={request.adults}&check_in={request.check_in}&check_out={request.check_out}",
                "image_url": "https://images.unsplash.com/photo-1542718610-a1d656d1884c?q=80&w=1000&auto=format&fit=crop",
                "price_per_night": 180.0,
                "total_price": 1260.0,
                "rating": 4.8,
                "reviews_count": 95,
                "room_type": "entire_home",
                "beds": 2,
                "bedrooms": 2,
                "bathrooms": 1.5,
                "amenities": ["Fireplace", "Hot tub", "Wifi", "Kitchen"],
                "location": request.location,
                "superhost": True
            }
        ]
        
        # Save mock data for future use
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mock_data_dir = os.path.join(base_dir, "api", "mock_data")
            os.makedirs(mock_data_dir, exist_ok=True)
            mock_data_path = os.path.join(mock_data_dir, "airbnb_listings.json")
            logger.info(f"Saving sample mock data to: {mock_data_path}")
            
            with open(mock_data_path, "w") as f:
                json.dump(mock_listings, f)
            logger.info("Successfully saved sample mock data")
        except Exception as e:
            logger.error(f"Error saving mock data: {str(e)}")
    else:
        # Update URLs in existing mock data to include query parameters
        logger.info("Updating URLs in existing mock data")
        for listing in mock_listings:
            listing_id = listing.get("id", "")
            if listing_id:
                listing["url"] = f"https://www.airbnb.com/rooms/{listing_id}?adults={request.adults}&check_in={request.check_in}&check_out={request.check_out}"
            listing["location"] = request.location
    
    # Filter by room type if specified
    if request.room_type:
        logger.info(f"Filtering by room type: {request.room_type}")
        mock_listings = [listing for listing in mock_listings if listing["room_type"] == request.room_type]
    
    # Filter by price range if specified
    if request.price_min is not None:
        logger.info(f"Filtering by minimum price: {request.price_min}")
        mock_listings = [listing for listing in mock_listings if listing["price_per_night"] >= request.price_min]
    if request.price_max is not None:
        logger.info(f"Filtering by maximum price: {request.price_max}")
        mock_listings = [listing for listing in mock_listings if listing["price_per_night"] <= request.price_max]
    
    logger.info(f"Returning {len(mock_listings)} mock listings")
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

@app.get("/airbnb/listing/{listing_id}/image")
async def get_listing_image(listing_id: str):
    """
    Get a specific Airbnb listing with its image formatted for display in the GPT chat.
    Returns markdown that can be used to display the image in the chat.
    """
    logger.info(f"Getting image for Airbnb listing {listing_id}")
    
    # Try to find the listing in our data
    listing = None
    
    # First check if we can get it from RapidAPI
    if RAPIDAPI_KEY:
        try:
            # Using ApiDojo's Airbnb API on RapidAPI to get listing details
            url = f"https://airbnb13.p.rapidapi.com/get-listing/{listing_id}"
            
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "airbnb13.p.rapidapi.com"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                logger.info(f"RapidAPI response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract the listing data
                    item = data.get("listing", {})
                    if item:
                        # Get the image URL from the API response
                        images = item.get("images", []) if isinstance(item.get("images"), list) else []
                        image_url = ""
                        if images and isinstance(images[0], dict):
                            image_url = images[0].get("picture", "")
                            logger.info(f"Found image URL (dict): {image_url}")
                        elif images and isinstance(images[0], str):
                            image_url = images[0]
                            logger.info(f"Found image URL (str): {image_url}")
                        
                        if image_url:
                            listing = {
                                "id": listing_id,
                                "name": item.get("name", "Beautiful Airbnb Listing"),
                                "image_url": image_url,
                                "url": f"https://www.airbnb.com/rooms/{listing_id}"
                            }
        except Exception as e:
            logger.error(f"Error fetching listing from RapidAPI: {str(e)}")
            # Continue to check mock data
    
    # If not found via RapidAPI, check mock data
    if not listing:
        logger.info("Falling back to mock data for image")
        mock_listings = load_mock_data("airbnb_listings.json")
        
        # Find the listing with the given ID
        for item in mock_listings:
            if item.get("id") == listing_id:
                listing = item
                logger.info(f"Found listing in mock data: {listing.get('name')}")
                break
    
    if not listing:
        logger.error(f"Listing with ID {listing_id} not found")
        raise HTTPException(status_code=404, detail=f"Listing with ID {listing_id} not found")
    
    # Get the image URL
    image_url = listing.get("image_url", "")
    if not image_url:
        logger.error(f"No image found for listing {listing_id}")
        raise HTTPException(status_code=404, detail=f"No image found for listing {listing_id}")
    
    logger.info(f"Returning image URL: {image_url}")
    
    # Ensure the image URL is using HTTPS
    if image_url.startswith("http:"):
        image_url = "https:" + image_url[5:]
    
    # Return the listing with image markdown
    return {
        "listing": listing,
        "markdown": f"![{listing['name']}]({image_url})",
        "image_url": image_url
    }

@app.post("/airbnb/listings/images")
async def get_listings_images(request: AirbnbListingRequest):
    """
    Get multiple Airbnb listings with their images formatted for display in the GPT chat.
    Returns markdown that can be used to display the images in the chat.
    """
    logger.info(f"Getting images for Airbnb listings in {request.location}")
    
    # Get listings based on the request
    listings = await search_airbnb_listings(request)
    
    # Limit to top 3 listings to avoid overwhelming the chat
    listings = listings[:3]
    
    # Format the response with markdown for each listing
    formatted_listings = []
    for listing in listings:
        image_url = listing.get("image_url", "")
        if image_url:
            # Ensure the image URL is using HTTPS
            if image_url.startswith("http:"):
                image_url = "https:" + image_url[5:]
                
            logger.info(f"Adding image for listing {listing.get('id')}: {image_url}")
            formatted_listings.append({
                "listing": listing,
                "markdown": f"![{listing['name']}]({image_url})",
                "image_url": image_url
            })
    
    logger.info(f"Returning {len(formatted_listings)} listing images")
    return {
        "listings": formatted_listings,
        "count": len(formatted_listings)
    }

@app.get("/airbnb/test-image")
async def test_image():
    """
    Test endpoint to verify that image URLs are working correctly.
    Returns a test image that should display in the GPT chat.
    """
    logger.info("Testing image display in GPT chat")
    
    # Use a reliable image URL from Unsplash
    test_image_url = "https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1000&auto=format&fit=crop"
    
    # Return the test image with markdown
    return {
        "markdown": f"![Test Image]({test_image_url})",
        "image_url": test_image_url,
        "message": "If you can see the image above, image display is working correctly."
    }

@app.get("/debug/files")
async def debug_files():
    """
    Debug endpoint to check the file system on the server.
    """
    logger.info("Checking file system")
    
    try:
        import os
        
        # Get the base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"Base directory: {base_dir}")
        
        # Check if the mock data directory exists
        mock_data_dir = os.path.join(base_dir, "api", "mock_data")
        mock_data_exists = os.path.exists(mock_data_dir)
        logger.info(f"Mock data directory exists: {mock_data_exists}")
        
        # List files in the mock data directory if it exists
        mock_data_files = []
        if mock_data_exists:
            mock_data_files = os.listdir(mock_data_dir)
            logger.info(f"Files in mock data directory: {mock_data_files}")
        
        # Check if the airbnb_listings.json file exists
        airbnb_listings_path = os.path.join(mock_data_dir, "airbnb_listings.json")
        airbnb_listings_exists = os.path.exists(airbnb_listings_path)
        logger.info(f"airbnb_listings.json exists: {airbnb_listings_exists}")
        
        # Get the size of the airbnb_listings.json file if it exists
        airbnb_listings_size = 0
        if airbnb_listings_exists:
            airbnb_listings_size = os.path.getsize(airbnb_listings_path)
            logger.info(f"airbnb_listings.json size: {airbnb_listings_size} bytes")
        
        # Try to read the airbnb_listings.json file if it exists
        airbnb_listings_content = []
        if airbnb_listings_exists:
            try:
                with open(airbnb_listings_path, "r") as f:
                    airbnb_listings_content = json.load(f)
                logger.info(f"Successfully read airbnb_listings.json: {len(airbnb_listings_content)} items")
            except Exception as e:
                logger.error(f"Error reading airbnb_listings.json: {str(e)}")
        
        # Return the debug information
        return {
            "base_dir": base_dir,
            "mock_data_dir": mock_data_dir,
            "mock_data_exists": mock_data_exists,
            "mock_data_files": mock_data_files,
            "airbnb_listings_exists": airbnb_listings_exists,
            "airbnb_listings_size": airbnb_listings_size,
            "airbnb_listings_count": len(airbnb_listings_content)
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 