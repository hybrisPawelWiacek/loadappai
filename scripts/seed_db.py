#!/usr/bin/env python
"""Script to seed the database with initial data."""
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.database import get_db
from src.infrastructure.seed_data import seed_all


def main():
    """Seed the database with initial data."""
    print("Starting database seeding...")
    
    with get_db() as db:
        try:
            seeded_data = seed_all(db)
            print("\nSeeded data summary:")
            for model, items in seeded_data.items():
                print(f"- {model}: {len(items)} items")
            print("\nDatabase seeding completed successfully!")
            
        except Exception as e:
            print(f"\nError seeding database: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
