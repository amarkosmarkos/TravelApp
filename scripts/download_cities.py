import pandas as pd
import requests
import zipfile
import io
import os
from pathlib import Path

def download_cities_data():
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # URL for the GeoNames cities dataset
    url = "https://download.geonames.org/export/dump/cities5000.zip"
    
    try:
        # Download the data
        print("Downloading cities data from GeoNames...")
        response = requests.get(url)
        response.raise_for_status()
        
        # Extract the zip file
        print("Extracting zip file...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Read the txt file directly from the zip
            with zip_ref.open('cities5000.txt') as file:
                # GeoNames format is tab-separated
                df = pd.read_csv(file, sep='\t', header=None, 
                               names=['geonameid', 'name', 'asciiname', 'alternatenames',
                                    'latitude', 'longitude', 'feature_class', 'feature_code',
                                    'country_code', 'cc2', 'admin1_code', 'admin2_code',
                                    'admin3_code', 'admin4_code', 'population', 'elevation',
                                    'dem', 'timezone', 'modification_date'])
        
        # Process the data
        print("Processing data...")
        # Select and rename columns to match our schema
        df = df.rename(columns={
            'name': 'name',
            'country_code': 'country',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'timezone': 'timezone',
            'population': 'population',
            'admin1_code': 'region'
        })
        
        # Select and reorder columns
        columns = ["name", "country", "latitude", "longitude", "timezone", "population", "region"]
        df = df[columns]
        
        # Save processed data
        processed_file = data_dir / "cities.csv"
        df.to_csv(processed_file, index=False)
        
        print(f"Data downloaded and processed successfully. Saved to {processed_file}")
        print(f"Total cities processed: {len(df)}")
        return processed_file
        
    except Exception as e:
        print(f"Error downloading or processing data: {e}")
        return None

if __name__ == "__main__":
    download_cities_data() 