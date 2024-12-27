# LoadApp.AI

A modern transport management system that helps calculate route costs and generate offers.

## Features

- Route planning with empty driving calculations
- Comprehensive cost calculations
- AI-enhanced offer generation
- Streamlit-based user interface

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp template.env .env
# Edit .env with your API keys and configuration
```

## Environment Configuration

The application uses environment variables for configuration. Copy `template.env` to `.env` and configure the following:

### Required Variables
- `OPENAI_API_KEY`: Your OpenAI API key for AI services
- `GOOGLE_MAPS_API_KEY`: Your Google Maps API key for location services
- `CREWAI_BEARER_TOKEN`: Your CrewAI Enterprise API token

### Optional Variables with Defaults

#### Backend Settings
- `BACKEND_HOST`: Host for the backend server (default: "localhost")
- `PORT`: Server port (default: 5001, avoid 5000 due to AirTunes conflict)
- `ENV`: Environment mode ["development", "staging", "production"] (default: "development")

#### API Configuration
- `OPENAI_MODEL`: OpenAI model to use (default: "gpt-4o-mini")
- `OPENAI_MAX_RETRIES`: Maximum OpenAI API retries (default: 3)
- `OPENAI_RETRY_DELAY`: Delay between retries in seconds (default: 1.0)
- `GMAPS_MAX_RETRIES`: Maximum Google Maps API retries (default: 2)
- `GMAPS_RETRY_DELAY`: Delay between retries in seconds (default: 0.1)
- `GMAPS_CACHE_TTL`: Cache time-to-live in seconds (default: 3600)
- `CREWAI_BASE_URL`: CrewAI Enterprise API URL (default: "https://api.crewai.com")

#### Feature Flags
- `WEATHER_ENABLED`: Enable weather data integration (default: false)
- `TRAFFIC_ENABLED`: Enable traffic data integration (default: false)
- `MARKET_DATA_ENABLED`: Enable market data integration (default: false)

4. Initialize the database:
```bash
python src/scripts/init_db.py
```

5. Run the application:
```bash
# Start the Flask backend
python run.py

# In a new terminal, start the Streamlit frontend
streamlit run src/frontend/app.py
```

## Project Structure

```
loadapp3/
├── src/
│   ├── domain/          # Domain entities and business logic
│   ├── infrastructure/  # Database, external services
│   ├── api/            # Flask API endpoints
│   └── frontend/       # Streamlit UI components
├── tests/              # Test suites
├── template.env        # Environment variable template
└── README.md          # This file
```

## Development

- Follow clean architecture principles
- Use type hints
- Write tests for core functionality
- Keep documentation up to date

## API Documentation

See `API_Specification.md` in the project documentation for detailed API endpoints.
