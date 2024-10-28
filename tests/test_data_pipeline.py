import pytest
from unittest.mock import patch, Mock, mock_open
from requests.exceptions import RequestException
from data_pipeline import DataPipeline

# Fixture to initialize the DataPipeline instance
@pytest.fixture
def pipeline():
    return DataPipeline()

# Fixture to provide sample data for tests
@pytest.fixture
def sample_data():
    return [{"id": 1, "name": "test"}]

# Test for successful data fetching from the API
@patch("requests.Session.get")  # Mock the get request in the requests.Session
def test_fetch_data_success(mock_get, pipeline, sample_data):
    """
    Test that data fetching is successful when the API responds correctly.
    """
    # Setup mock response with status code 200 and sample JSON data
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_data
    mock_get.return_value = mock_response
    
    # Call fetch_data and assert it returns the expected data
    data = pipeline.fetch_data("tracks")
    assert data == sample_data
    mock_get.assert_called_once_with("http://127.0.0.1:8000/tracks")  # Verify endpoint URL

# Test for handling network errors during data fetching
@patch("requests.Session.get")
def test_fetch_data_network_error(mock_get, pipeline):
    """
    Test that fetch_data handles network-related exceptions.
    """
    # Simulate a network error using side_effect
    mock_get.side_effect = RequestException("Network error")
    
    # Verify that fetch_data raises RequestException when a network error occurs
    with pytest.raises(RequestException, match="Network error"):
        pipeline.fetch_data("tracks")

# Test for handling invalid JSON responses from the API
@patch("requests.Session.get")
def test_fetch_data_invalid_json(mock_get, pipeline):
    """
    Test that fetch_data raises a ValueError when the response is not valid JSON.
    """
    # Setup mock response to raise a JSON decoding error
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response
    
    # Verify that ValueError is raised due to invalid JSON response
    with pytest.raises(ValueError, match="Invalid JSON"):
        pipeline.fetch_data("tracks")

# Test for unexpected data formats in the API response
@patch("requests.Session.get")
def test_fetch_data_unexpected_format(mock_get, pipeline):
    """
    Test that fetch_data raises a ValueError if the response is not in expected format.
    """
    # Setup mock response with unexpected data format
    mock_response = Mock()
    mock_response.json.return_value = "not a list or dict"
    mock_get.return_value = mock_response
    
    # Verify that a ValueError is raised for unexpected response format
    with pytest.raises(ValueError, match="Unexpected data format"):
        pipeline.fetch_data("tracks")

# Test for successful data saving to a JSON file
@patch("builtins.open", new_callable=mock_open)  # Mock open to prevent actual file writing
@patch("os.path.getsize", return_value=100)      # Mock getsize to simulate file size
def test_save_data_success(mock_getsize, mock_file, pipeline, sample_data):
    """
    Test that save_data successfully writes data to a file with correct filename.
    """
    # Call save_data and verify filepath contains the correct filename and extension
    filepath = pipeline.save_data(sample_data, "test")
    assert "test_" in filepath
    assert filepath.endswith(".json")
    mock_file.assert_called_once()  # Verify file was opened once

# Test for handling non-serializable data during saving
def test_save_data_non_serializable(pipeline):
    """
    Test that save_data raises a TypeError if data cannot be serialized to JSON.
    """
    # Attempt to save non-serializable data and expect a TypeError
    non_serializable_data = {"key": object()}
    with pytest.raises(TypeError):
        pipeline.save_data(non_serializable_data, "test")

# Test for handling file write errors during saving
@patch("builtins.open", side_effect=IOError("Write error"))
def test_save_data_write_error(mock_file, pipeline, sample_data):
    """
    Test that save_data raises an IOError if there is a file write error.
    """
    # Attempt to save data and expect IOError due to simulated write error
    with pytest.raises(IOError, match="Write error"):
        pipeline.save_data(sample_data, "test")

# Test for successful pipeline execution
@patch("data_pipeline.DataPipeline.fetch_data")  # Mock fetch_data to avoid actual API calls
@patch("data_pipeline.DataPipeline.save_data")   # Mock save_data to avoid actual file writes
def test_run_pipeline_success(mock_save, mock_fetch, pipeline, sample_data):
    """
    Test that run_pipeline executes the pipeline successfully, fetching and saving data.
    """
    # Setup mock responses for fetch_data and save_data
    mock_fetch.return_value = sample_data
    mock_save.return_value = "test_file.json"
    
    # Execute the pipeline and verify the results
    results = pipeline.run_pipeline()
    assert len(results) == 3  # Ensure all endpoints were processed
    assert all(isinstance(v, str) for v in results.values())  # Check if paths are strings
    assert mock_fetch.call_count == 3  # Verify fetch_data called for each endpoint
    assert mock_save.call_count == 3  # Verify save_data called for each endpoint

# Test for error handling during pipeline execution
@patch("data_pipeline.DataPipeline.fetch_data")
def test_run_pipeline_error(mock_fetch, pipeline):
    """
    Test that run_pipeline handles errors gracefully by raising exceptions.
    """
    # Simulate an error in fetch_data
    mock_fetch.side_effect = Exception("Pipeline error")
    
    # Verify that an exception is raised with the expected message
    with pytest.raises(Exception, match="Pipeline error"):
        pipeline.run_pipeline()
