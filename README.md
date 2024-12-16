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
cp .env.example .env
# Edit .env with your API keys
```

4. Initialize the database:
```bash
python src/scripts/init_db.py
```

5. Run the application:
```bash
# Start the Flask backend
python src/backend/app.py

# In a new terminal, start the Streamlit frontend
streamlit run src/frontend/app.py
```

## Project Structure

```
loadapp3/
├── src/
│   ├── domain/          # Domain entities and business logic
│   ├── infrastructure/  # Database, external services
│   ├── application/     # Use cases and services
│   ├── backend/         # Flask API
│   ├── frontend/        # Streamlit UI
│   └── scripts/         # Utility scripts
├── tests/              # Test files
├── requirements.txt    # Project dependencies
└── .env               # Environment variables
```

## Development

- Follow clean architecture principles
- Use type hints
- Write tests for core functionality
- Keep documentation up to date

## API Documentation

See `API_Specification.md` in the project documentation for detailed API endpoints.
