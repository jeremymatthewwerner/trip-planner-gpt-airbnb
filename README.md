# Trip Planner GPT with Airbnb Integration

A custom OpenAI GPT that helps users plan trips with personalized itineraries and Airbnb accommodation recommendations.

## Try It Out

You can try the Vacation Rental Trip Planner GPT here:
[Vacation Rental Trip Planner GPT](https://chatgpt.com/g/g-67d4c4b0ed64819195294fda4747b6ca-vacation-rental-trip-planner/c/67d4ccba-3c10-800c-857f-79dfcc4b537c)

## Overview

This project consists of:

1. **API Backend**: A FastAPI application that provides endpoints for:
   - Searching Airbnb listings (using RapidAPI)
   - Finding attractions at destinations
   - Creating personalized trip itineraries

2. **Custom GPT Configuration**: Files needed to create a custom GPT in OpenAI's GPT Builder:
   - Instructions for the GPT
   - OpenAPI specification for connecting to the API

3. **Automation Tools**: Scripts to automate the GPT Builder interface:
   - Playwright script to update the GPT configuration programmatically
   - Handles updating OpenAPI schema and GPT settings

## Features

- **Personalized Trip Planning**: Create custom itineraries based on user preferences and travel dates
- **Airbnb Integration**: Search for accommodations with filters for dates, location, price, and room type
- **Attraction Recommendations**: Discover popular attractions and activities at your destination
- **Visual Listings**: Display Airbnb listing images directly in the chat for a more engaging experience
- **Smart URL Generation**: Airbnb listing links include date and guest parameters for a seamless booking experience

## Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API key
- RapidAPI key (for Airbnb data)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/trip-planner-gpt-airbnb.git
   cd trip-planner-gpt-airbnb
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```

5. Add your API keys to the `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   RAPIDAPI_KEY=your_rapidapi_key_here
   ```

### Running the API Locally

```
cd api
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## Deploying the API

### Option 1: Deploying to Render (Recommended)

1. **Create a Render Account**:
   - Sign up at [Render](https://render.com/) if you don't have an account

2. **Push Your Code to GitHub**:
   - Create a GitHub repository
   - Push your code to the repository
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/trip-planner-gpt-airbnb.git
   git push -u origin main
   ```

3. **Create a New Web Service on Render**:
   - From your Render dashboard, click "New" and select "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: trip-planner-api (or any name you prefer)
     - **Environment**: Python
     - **Region**: Choose the closest to your target users
     - **Branch**: main
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `cd api && uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Free (or select a paid plan if needed)

4. **Add Environment Variables**:
   - In the "Environment" section, add:
     - `RAPIDAPI_KEY`: Your RapidAPI key
     - `OPENAI_API_KEY`: Your OpenAI API key

5. **Deploy the Service**:
   - Click "Create Web Service"
   - Wait for the deployment to complete (usually takes a few minutes)
   - Your API will be available at `https://your-service-name.onrender.com`

### Option 2: Deploying to Railway

1. **Create a Railway Account**:
   - Sign up at [Railway](https://railway.app/) if you don't have an account

2. **Push Your Code to GitHub**:
   - Follow the same steps as for Render

3. **Create a New Project on Railway**:
   - From your Railway dashboard, click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub repository
   - Configure the service:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `cd api && uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**:
   - In the "Variables" section, add:
     - `RAPIDAPI_KEY`: Your RapidAPI key
     - `OPENAI_API_KEY`: Your OpenAI API key

5. **Deploy the Service**:
   - Railway will automatically deploy your service
   - Your API will be available at the URL provided by Railway

### Option 3: Deploying to Fly.io

1. **Install Flyctl**:
   - Follow the instructions at [Fly.io](https://fly.io/docs/hands-on/install-flyctl/)

2. **Login to Fly.io**:
   ```
   flyctl auth login
   ```

3. **Create a fly.toml File**:
   ```
   [build]
   builder = "paketobuildpacks/builder:base"

   [env]
   PORT = "8080"

   [http_service]
   internal_port = 8080
   force_https = true
   auto_stop_machines = true
   auto_start_machines = true
   min_machines_running = 0
   ```

4. **Deploy to Fly.io**:
   ```
   flyctl launch
   ```

5. **Set Environment Variables**:
   ```
   flyctl secrets set RAPIDAPI_KEY=your_rapidapi_key_here
   flyctl secrets set OPENAI_API_KEY=your_openai_api_key_here
   ```

## After Deployment

1. **Update the OpenAPI Specification**:
   - Open `gpt_config/openapi.yaml`
   - Update the server URL with your deployed API URL:
   ```yaml
   servers:
     - url: https://your-deployed-api-url.com
       description: Production server
   ```

2. **Commit and Push the Changes**:
   ```
   git add gpt_config/openapi.yaml
   git commit -m "Update API URL"
   git push
   ```

## Automating GPT Updates

This project includes a Playwright automation script to update your GPT configuration programmatically, avoiding the need to manually update through the web interface.

### Setup Automation

1. **Navigate to the automation directory**:
   ```
   cd automation
   ```

2. **Install dependencies**:
   ```
   npm install
   ```

3. **Create a .env file**:
   ```
   cp .env.example .env
   ```

4. **Edit the .env file** with your OpenAI credentials and GPT information:
   ```
   OPENAI_EMAIL=your_email@example.com
   OPENAI_PASSWORD=your_password
   GPT_ID=g-your-gpt-id
   GPT_NAME="Your GPT Name"
   OPENAPI_SCHEMA_PATH="../gpt_config/openapi.yaml"
   CONFIG_JSON_PATH="../gpt_config/config.json"
   ```

### Running the Automation

Run the script to update your GPT:

```
npm run update
```

The script will:
- Log in to your OpenAI account
- Navigate to your GPT in the GPT Builder
- Update the OpenAPI schema
- Optionally update the GPT configuration (name, description, instructions)
- Save the changes

### Options

- `--headless=false` (default): Run with a visible browser to monitor progress
- `--wait-for-captcha=true` (default): Pause for manual CAPTCHA solving if needed
- `--schema=path/to/schema.yaml`: Specify a custom path to the OpenAPI schema
- `--config=path/to/config.json`: Specify a custom path to the GPT configuration

For more details, see the [automation README](automation/README.md).

## Creating the Custom GPT

1. **Go to OpenAI GPT Builder**:
   - Visit [OpenAI GPT Builder](https://chat.openai.com/gpt-builder)
   - Sign in with your OpenAI account

2. **Create a New GPT**:
   - Click "Create a GPT"
   - In the configuration panel:
     - **Name**: "Trip Planner with Airbnb"
     - **Description**: "A specialized GPT that helps you plan trips using Airbnb listings and local attractions."
     - **Instructions**: Copy the content from `gpt_config/config.json` (the "instructions" field)
     - **Conversation starters**: Add example prompts (see below)

3. **Configure Capabilities**:
   - Enable "Web Browsing" (for searching Airbnb.com when needed)
   - Enable "DALL-E Image Generation" (for generating images of destinations)

4. **Add Actions (API Integration)**:
   - Click "Actions"
   - Click "Add action"
   - Select "Upload an OpenAPI schema"
   - Upload the `gpt_config/openapi.yaml` file
   - Click "Save"

5. **Test Your GPT**:
   - Use the preview to test your GPT with various travel planning scenarios
   - Make adjustments as needed

6. **Publish Your GPT** (Optional):
   - Click "Publish"
   - Choose whether to make it public or private
   - Complete any additional required information

## Example Prompts

- "Plan a 5-day trip to Paris for 2 adults with a budget of $2000"
- "Find Airbnb options in Tokyo for next month"
- "What are the must-see attractions in Barcelona?"
- "Create an itinerary for my honeymoon in Bali"
- "I want to visit New York in December. What should I pack?"

## API Endpoints

- `POST /airbnb/search`: Search for Airbnb listings
- `POST /attractions/search`: Search for attractions
- `POST /itinerary/create`: Create a trip itinerary
- `GET /airbnb/listing/{listing_id}/image`: Get a specific Airbnb listing with its image formatted for display in the GPT chat
- `POST /airbnb/listings/images`: Get multiple Airbnb listings with their images formatted for display in the GPT chat

## Troubleshooting

- **API Key Issues**: If you're getting authentication errors, double-check your API keys in the environment variables.
- **Deployment Failures**: Check the logs in your deployment platform for specific error messages.
- **CORS Errors**: The API has CORS middleware enabled, but if you're experiencing issues, check the CORS configuration.
- **RapidAPI Rate Limits**: Be aware of the rate limits for your RapidAPI subscription tier.

## License

MIT 