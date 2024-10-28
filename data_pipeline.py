import requests
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Union
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure logging to file and console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),  # Log file output
        logging.StreamHandler()               # Console output
    ]
)
logger = logging.getLogger(__name__)

class DataPipeline:
    """
    A class to handle data fetching and saving from APIs
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialize the DataPipeline with a base URL and configure an HTTP session
        with retry strategy.

        Args:
            base_url (str): The base URL of the API
        """
        self.base_url = base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Create a session with a retry strategy to handle temporary network issues.

        Returns:
            requests.Session: Configured session with retries
        """
        session = requests.Session()
        
        # Define retry strategy with status codes and retry intervals
        retry_strategy = Retry(
            total=3,                        # Retry up to 3 times
            backoff_factor=1,               # Backoff time between retries
            status_forcelist=[429, 500, 502, 503, 504]  # Retry on these HTTP codes
        )
        
        # Apply retry strategy to both HTTP and HTTPS adapters
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_data(self, endpoint: str) -> Union[List, Dict]:
        """
        Fetch data from a specified API endpoint.

        Args:
            endpoint (str): API endpoint to fetch data from

        Returns:
            Union[List, Dict]: Parsed JSON response data

        Raises:
            requests.exceptions.RequestException: If the HTTP request fails
            ValueError: If the response format is not JSON-compatible
        """
        url = f"{self.base_url}/{endpoint}"  # Construct full URL
        start_time = datetime.now()          # Record start time for performance logging

        try:
            logger.info(f"Fetching data from {endpoint}")
            
            # Perform the GET request
            response = self.session.get(url)
            response.raise_for_status()      # Raise exception for HTTP errors
            
            # Parse JSON response and validate data format
            data = response.json()
            if not isinstance(data, (list, dict)):
                raise ValueError(f"Unexpected data format from {endpoint}")
            
            # Log fetch duration and data size
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
        Save the fetched data as a JSON file with a timestamped filename.

        Args:
            data (Union[List, Dict]): Data to be saved
            filename (str): Base filename to use for saved file

        Returns:
            str: Path to the saved file

        Raises:
            TypeError: If the data is not JSON serializable
            IOError: If file cannot be written
        """
        try:
            # Validate that data is JSON serializable
            json.dumps(data)

            # Generate a timestamped file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("data", exist_ok=True)  # Ensure data directory exists
            filepath = os.path.join("data", f"{filename}_{timestamp}.json")
            
            # Write data to JSON file with indentation for readability
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
            
            # Log saved file size for reference
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
        Run the data pipeline, fetching and saving data for each endpoint.

        Returns:
            Dict[str, str]: Mapping of endpoint names to file paths of saved data

        Raises:
            Exception: If any part of the pipeline fails
        """
        endpoints = ["tracks", "users", "listen_history"]  # Define endpoints to fetch
        results = {}

        try:
            for endpoint in endpoints:
                # Fetch data from endpoint and save it to a file
                data = self.fetch_data(endpoint)
                filepath = self.save_data(data, endpoint)
                results[endpoint] = filepath  # Store filepath in results
            
            logger.info("Pipeline completed successfully")
            return results

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise

# Execute the data pipeline if the script is run directly
if __name__ == "__main__":
    try:
        pipeline = DataPipeline()          # Instantiate pipeline
        results = pipeline.run_pipeline()  # Run the pipeline
        print("Pipeline completed. Files saved:")
        
        # Display each endpoint and its corresponding saved file path
        for endpoint, filepath in results.items():
            print(f"{endpoint}: {filepath}")
    
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise
