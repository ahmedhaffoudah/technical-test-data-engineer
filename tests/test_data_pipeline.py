import pytest
from unittest.mock import patch, Mock, mock_open
from requests.exceptions import RequestException
from data_pipeline import DataPipeline

@pytest.fixture
def pipeline():
    return DataPipeline()

@pytest.fixture
def sample_data():
    return [{"id": 1, "name": "test"}]

# Test successful data fetching
@patch("requests.Session.get")
def test_fetch_data_success(mock_get, pipeline, sample_data):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_data
    mock_get.return_value = mock_response
    
    data = pipeline.fetch_data("tracks")
    assert data == sample_data
    mock_get.assert_called_once_with("http://127.0.0.1:8000/tracks")

# Test network error handling
@patch("requests.Session.get")
def test_fetch_data_network_error(mock_get, pipeline):
    mock_get.side_effect = RequestException("Network error")
    
    with pytest.raises(RequestException, match="Network error"):
        pipeline.fetch_data("tracks")

# Test invalid JSON response
@patch("requests.Session.get")
def test_fetch_data_invalid_json(mock_get, pipeline):
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response
    
    with pytest.raises(ValueError, match="Invalid JSON"):
        pipeline.fetch_data("tracks")

# Test unexpected response format
@patch("requests.Session.get")
def test_fetch_data_unexpected_format(mock_get, pipeline):
    mock_response = Mock()
    mock_response.json.return_value = "not a list or dict"
    mock_get.return_value = mock_response
    
    with pytest.raises(ValueError, match="Unexpected data format"):
        pipeline.fetch_data("tracks")

# Test successful data saving with mock for file size
@patch("builtins.open", new_callable=mock_open)
@patch("os.path.getsize", return_value=100)  # Mock getsize to return a dummy file size
def test_save_data_success(mock_getsize, mock_file, pipeline, sample_data):
    filepath = pipeline.save_data(sample_data, "test")
    assert "test_" in filepath
    assert filepath.endswith(".json")
    mock_file.assert_called_once()

# Test non-serializable data
def test_save_data_non_serializable(pipeline):
    non_serializable_data = {"key": object()}
    
    with pytest.raises(TypeError):
        pipeline.save_data(non_serializable_data, "test")

# Test file write error
@patch("builtins.open", side_effect=IOError("Write error"))
def test_save_data_write_error(mock_file, pipeline, sample_data):
    with pytest.raises(IOError, match="Write error"):
        pipeline.save_data(sample_data, "test")

# Test complete pipeline execution
@patch("data_pipeline.DataPipeline.fetch_data")
@patch("data_pipeline.DataPipeline.save_data")
def test_run_pipeline_success(mock_save, mock_fetch, pipeline, sample_data):
    mock_fetch.return_value = sample_data
    mock_save.return_value = "test_file.json"
    
    results = pipeline.run_pipeline()
    assert len(results) == 3
    assert all(isinstance(v, str) for v in results.values())
    assert mock_fetch.call_count == 3
    assert mock_save.call_count == 3

# Test pipeline error handling
@patch("data_pipeline.DataPipeline.fetch_data")
def test_run_pipeline_error(mock_fetch, pipeline):
    mock_fetch.side_effect = Exception("Pipeline error")
    
    with pytest.raises(Exception, match="Pipeline error"):
        pipeline.run_pipeline()
