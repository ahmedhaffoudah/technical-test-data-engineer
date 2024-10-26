import sys
import os
import pytest
import json
from unittest.mock import patch, Mock

# Add the root directory to the path for importing data_pipeline.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_pipeline import fetch_data, save_data

# Test for API Data Retrieval
@patch("data_pipeline.requests.get")
def test_fetch_data(mock_get):
    # Mock response for successful data retrieval
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1, "name": "sample track"}]  # Example response
    mock_get.return_value = mock_response

    data = fetch_data("tracks")
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "sample track"

    # Mock response for an empty response
    mock_response.json.return_value = []
    data = fetch_data("tracks")
    assert data == []

# Test for Data Saving
def test_save_data():
    sample_data = {"sample": "data"}
    save_data(sample_data, "test_data")

    # Check that the file is created
    files = [f for f in os.listdir("data") if f.startswith("test_data")]
    assert len(files) > 0

    # Validate file content
    with open(os.path.join("data", files[0]), "r") as f:
        data = json.load(f)
    assert data == sample_data

    # Clean up after test
    for f in files:
        os.remove(os.path.join("data", f))

# Test for Error Handling in fetch_data
@patch("data_pipeline.requests.get")
def test_fetch_data_error_handling(mock_get):
    # Simulate a failed request
    mock_get.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        fetch_data("invalid_endpoint")
