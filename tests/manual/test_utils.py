"""Common utilities for manual tests."""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_env():
    """Load environment variables from .env file.
    
    Searches for .env file in project root directory.
    """
    # Find project root (where .env is located)
    current_dir = Path(__file__).parent
    while current_dir.name != "loadapp3" and current_dir.parent != current_dir:
        current_dir = current_dir.parent
    
    env_path = current_dir / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found in {current_dir}")
        
    # Load environment variables
    load_dotenv(env_path)
    
def get_required_env(name: str) -> str:
    """Get required environment variable.
    
    Args:
        name: Name of environment variable
        
    Returns:
        Value of environment variable
        
    Raises:
        ValueError: If environment variable is not set
    """
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable {name} not set")
    return value
