import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
import sys

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.models.city import City
from app.database import Base, SQLALCHEMY_DATABASE_URL

def load_cities_to_db():
    # Create database engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Read the CSV file
        csv_path = Path("data/cities.csv")
        if not csv_path.exists():
            print("Cities CSV file not found. Please run download_cities.py first.")
            return
        
        df = pd.read_csv(csv_path)
        
        # Insert data into database
        for _, row in df.iterrows():
            city = City(
                name=row['name'],
                country=row['country'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                timezone=row['timezone'],
                population=row['population'] if pd.notna(row['population']) else None,
                region=row['region']
            )
            db.add(city)
        
        # Commit the changes
        db.commit()
        print("Cities data loaded successfully into the database.")
        
        # Verify the data
        count = db.query(City).count()
        print(f"Total cities in database: {count}")
        
    except Exception as e:
        print(f"Error loading data into database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_cities_to_db() 