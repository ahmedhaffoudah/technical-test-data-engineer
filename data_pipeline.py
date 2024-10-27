import requests
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Union
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_data(self, endpoint: str) -> Union[List, Dict]:
        """
        Fetch data from specified endpoint with improved error handling
        
        Args:
            endpoint: API endpoint to fetch data from
            
        Returns:
            Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException: If request fails
            ValueError: If response format is invalid
        """
        url = f"{self.base_url}/{endpoint}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Fetching data from {endpoint}")
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            if not isinstance(data, (list, dict)):
                raise ValueError(f"Unexpected data format from {endpoint}")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully fetched {len(str(data))} bytes from {endpoint} in {duration:.2f} seconds")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from {endpoint}: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Error parsing data from {endpoint}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching from {endpoint}: {str(e)}")
            raise

    def save_data(self, data: Union[List, Dict], filename: str) -> str:
        """
        Save data to JSON file with timestamp
        
        Args:
            data: Data to save
            filename: Base filename
            
        Returns:
            Path to saved file
            
        Raises:
            TypeError: If data is not JSON serializable
            IOError: If file cannot be written
        """
        try:
            # Validate JSON serialization
            json.dumps(data)
            
            # Create timestamp and filepath
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("data", exist_ok=True)
            filepath = os.path.join("data", f"{filename}_{timestamp}.json")
            
            # Save file
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
                
            file_size = os.path.getsize(filepath)
            logger.info(f"Successfully saved {file_size} bytes to {filepath}")
            
            return filepath
            
        except TypeError as e:
            logger.error(f"Data for {filename} is not JSON serializable: {str(e)}")
            raise
        except IOError as e:
            logger.error(f"Error saving data to {filename}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while saving {filename}: {str(e)}")
            raise

    def run_pipeline(self) -> Dict[str, str]:
        """
        Run the complete pipeline for all endpoints
        
        Returns:
            Dictionary mapping endpoint names to saved file paths
        """
        endpoints = ["tracks", "users", "listen_history"]
        results = {}
        
        try:
            for endpoint in endpoints:
                data = self.fetch_data(endpoint)
                filepath = self.save_data(data, endpoint)
                results[endpoint] = filepath
                
            logger.info("Pipeline completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        pipeline = DataPipeline()
        results = pipeline.run_pipeline()
        print("Pipeline completed. Files saved:")
        for endpoint, filepath in results.items():
            print(f"{endpoint}: {filepath}")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise