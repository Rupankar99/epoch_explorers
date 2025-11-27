"""
Data Sources and Web API Integration for Clusterer

Provides modular, non-breaking web data acquisition capabilities.
Can be used with or without the main clusterer pipeline.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Supported data source types"""
    REST_API = "rest_api"
    JSON_URL = "json_url"
    CSV_URL = "csv_url"
    DATABASE = "database"
    DIRECT_INPUT = "direct_input"  # Default MVP


@dataclass
class APIRequest:
    """Configuration for API requests"""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Optional[Dict[str, Any]] = None
    json_body: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retry_count: int = 3
    
    def __post_init__(self):
        """Set default headers"""
        if not self.headers:
            self.headers = {
                "User-Agent": "EpochExplorers/1.0",
                "Accept": "application/json"
            }


@dataclass
class APIResponse:
    """Structured API response"""
    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_text: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if response was successful"""
        return 200 <= self.status_code < 300 and self.error is None


class WebDataSource:
    """Fetch and standardize data from web sources"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize web data source client
        
        Args:
            verbose: Enable logging
        """
        self.verbose = verbose
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Context manager entry"""
        if HAS_HTTPX:
            self.session = httpx.AsyncClient(verify=False, timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.aclose()
    
    def _log(self, message: str, level: str = "info"):
        """Log if verbose"""
        if self.verbose:
            getattr(logger, level)(f"[WebDataSource] {message}")
    
    async def fetch_json_api(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET"
    ) -> APIResponse:
        """
        Fetch JSON data from REST API
        
        Args:
            url: API endpoint URL
            params: Query parameters
            headers: Custom headers
            method: HTTP method (GET, POST, etc.)
        
        Returns:
            APIResponse with structured data
        
        Example:
            ```python
            async with WebDataSource() as source:
                response = await source.fetch_json_api(
                    "https://api.example.com/incidents",
                    params={"limit": 100}
                )
                data = response.data  # Parsed JSON
            ```
        """
        if not HAS_HTTPX:
            return APIResponse(
                status_code=0,
                data={},
                headers={},
                error="httpx not installed"
            )
        
        if not self.session:
            return APIResponse(
                status_code=0,
                data={},
                headers={},
                error="WebDataSource not initialized with context manager"
            )
        
        try:
            self._log(f"Fetching {method} {url}")
            
            response = await self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers or {}
            )
            
            self._log(f"Response status: {response.status_code}")
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = {"raw_text": response.text}
            
            return APIResponse(
                status_code=response.status_code,
                data=data,
                headers=dict(response.headers),
                raw_text=response.text
            )
        
        except Exception as e:
            self._log(f"Error fetching data: {str(e)}", "error")
            return APIResponse(
                status_code=0,
                data={},
                headers={},
                error=str(e)
            )
    
    async def fetch_multiple_apis(
        self,
        requests: List[APIRequest]
    ) -> Dict[str, APIResponse]:
        """
        Fetch data from multiple APIs concurrently
        
        Args:
            requests: List of APIRequest configurations
        
        Returns:
            Dictionary mapping request URLs to responses
        
        Example:
            ```python
            requests = [
                APIRequest("https://api1.example.com/data"),
                APIRequest("https://api2.example.com/data")
            ]
            responses = await source.fetch_multiple_apis(requests)
            # responses = {
            #     "https://api1.example.com/data": APIResponse(...),
            #     "https://api2.example.com/data": APIResponse(...)
            # }
            ```
        """
        tasks = [
            self.fetch_json_api(
                req.url,
                params=req.params,
                headers=req.headers,
                method=req.method
            )
            for req in requests
        ]
        
        responses = await asyncio.gather(*tasks)
        return {req.url: resp for req, resp in zip(requests, responses)}
    
    async def fetch_first_available_api(
        self,
        requests: List[APIRequest],
        min_records: int = 1
    ) -> APIResponse:
        """
        Try multiple APIs sequentially, skip empty/failed ones, return first successful
        
        Args:
            requests: List of APIRequest configurations to try in order
            min_records: Minimum number of records required (skip if fewer)
        
        Returns:
            First successful APIResponse with data, or error response if all fail
        
        Example:
            ```python
            requests = [
                APIRequest("https://api1.example.com/data"),
                APIRequest("https://api2.example.com/data"),
                APIRequest("https://api3.example.com/data")
            ]
            # Tries api1, if empty/error tries api2, if empty/error tries api3
            response = await source.fetch_first_available_api(requests)
            if response.success and response.data:
                use_data(response.data)
            ```
        """
        for i, req in enumerate(requests, 1):
            self._log(f"Attempt {i}/{len(requests)}: Fetching from {req.url}")
            
            try:
                response = await self.fetch_json_api(
                    req.url,
                    params=req.params,
                    headers=req.headers,
                    method=req.method
                )
                
                # Check if response successful
                if not response.success:
                    self._log(f"  ✗ Failed (status {response.status_code}): {response.error}", "warning")
                    continue
                
                # Check if response has data
                if not response.data or (isinstance(response.data, dict) and len(response.data) == 0):
                    self._log(f"  ✗ Empty response, skipping", "warning")
                    continue
                
                # Check if has minimum records
                if isinstance(response.data, dict):
                    # If data is wrapped in a list or has records field
                    record_count = 0
                    if "records" in response.data:
                        record_count = len(response.data.get("records", []))
                    elif "data" in response.data:
                        record_count = len(response.data.get("data", []))
                    elif "items" in response.data:
                        record_count = len(response.data.get("items", []))
                    else:
                        # Just count keys as records
                        record_count = len(response.data)
                    
                    if record_count < min_records:
                        self._log(f"  ✗ Insufficient records ({record_count} < {min_records}), skipping", "warning")
                        continue
                
                # Success!
                self._log(f"  ✓ Success! Got data from {req.url}")
                return response
            
            except Exception as e:
                self._log(f"  ✗ Exception: {str(e)}", "warning")
                continue
        
        # All failed
        self._log(f"All {len(requests)} APIs failed or returned empty data", "error")
        return APIResponse(
            status_code=0,
            data={},
            headers={},
            error=f"All {len(requests)} APIs failed or returned empty data"
        )
    
    async def fetch_csv_data(
        self,
        url: str
    ) -> Dict[str, Any]:
        """
        Fetch and parse CSV data from URL
        
        Args:
            url: CSV file URL
        
        Returns:
            Dictionary with parsed CSV data
        
        Example:
            ```python
            data = await source.fetch_csv_data("https://example.com/data.csv")
            # data = {
            #     "headers": ["col1", "col2", ...],
            #     "rows": [[val1, val2, ...], ...],
            #     "row_count": 1000
            # }
            ```
        """
        if not HAS_HTTPX or not self.session:
            return {"error": "HTTP client not available"}
        
        try:
            self._log(f"Fetching CSV from {url}")
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            # Simple CSV parsing
            lines = response.text.strip().split('\n')
            if not lines:
                return {"error": "Empty CSV file"}
            
            headers = lines[0].split(',')
            rows = [line.split(',') for line in lines[1:]]
            
            return {
                "headers": headers,
                "rows": rows,
                "row_count": len(rows),
                "column_count": len(headers)
            }
        
        except Exception as e:
            self._log(f"CSV fetch error: {str(e)}", "error")
            return {"error": str(e)}


@dataclass
class DataSourceConfig:
    """Configuration for data source"""
    source_type: DataSourceType
    url: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    database_path: Optional[str] = None
    table_name: Optional[str] = None
    direct_data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    method: str = "GET"
    timeout: int = 30


class DataSourceFactory:
    """Factory for creating data source clients"""
    
    @staticmethod
    async def fetch_data(
        config: DataSourceConfig
    ) -> Dict[str, Any]:
        """
        Fetch data based on configuration
        
        Args:
            config: DataSourceConfig specifying source type and parameters
        
        Returns:
            Fetched and standardized data
        
        Example:
            ```python
            # From REST API
            config = DataSourceConfig(
                source_type=DataSourceType.REST_API,
                url="https://api.example.com/incidents",
                params={"limit": 100}
            )
            data = await DataSourceFactory.fetch_data(config)
            
            # From direct input
            config = DataSourceConfig(
                source_type=DataSourceType.DIRECT_INPUT,
                direct_data={"col1": [...], "col2": [...]}
            )
            data = await DataSourceFactory.fetch_data(config)
            ```
        """
        if config.source_type == DataSourceType.DIRECT_INPUT:
            return config.direct_data or {}
        
        elif config.source_type == DataSourceType.REST_API:
            if not config.url:
                return {"error": "URL required for REST API"}
            
            async with WebDataSource() as source:
                response = await source.fetch_json_api(
                    url=config.url,
                    params=config.params,
                    headers=config.headers,
                    method=config.method
                )
                
                if response.success:
                    return response.data
                else:
                    return {"error": response.error}
        
        elif config.source_type == DataSourceType.JSON_URL:
            if not config.url:
                return {"error": "URL required for JSON data"}
            
            async with WebDataSource() as source:
                response = await source.fetch_json_api(url=config.url)
                
                if response.success:
                    return response.data
                else:
                    return {"error": response.error}
        
        elif config.source_type == DataSourceType.CSV_URL:
            if not config.url:
                return {"error": "URL required for CSV data"}
            
            async with WebDataSource() as source:
                return await source.fetch_csv_data(config.url)
        
        else:
            return {"error": f"Unsupported source type: {config.source_type}"}


# Convenience functions
async def fetch_from_api(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Quick function to fetch JSON from API
    
    Example:
        ```python
        data = await fetch_from_api(
            "https://api.example.com/incidents",
            params={"limit": 100}
        )
        ```
    """
    config = DataSourceConfig(
        source_type=DataSourceType.REST_API,
        url=url,
        params=params,
        headers=headers
    )
    return await DataSourceFactory.fetch_data(config)


async def fetch_from_csv(url: str) -> Dict[str, Any]:
    """
    Quick function to fetch CSV from URL
    
    Example:
        ```python
        data = await fetch_from_csv("https://example.com/data.csv")
        ```
    """
    config = DataSourceConfig(
        source_type=DataSourceType.CSV_URL,
        url=url
    )
    return await DataSourceFactory.fetch_data(config)


if __name__ == "__main__":
    """Example usage"""
    
    async def example():
        # Example 1: Fetch from JSON API
        print("Example 1: Fetch from JSON API")
        data = await fetch_from_api(
            "https://jsonplaceholder.typicode.com/posts",
            params={"_limit": 5}
        )
        print(f"Fetched {len(data)} posts")
        
        # Example 2: Fetch from CSV
        print("\nExample 2: Fetch from CSV")
        data = await fetch_from_csv(
            "https://example.com/data.csv"
        )
        print(f"CSV data: {data}")
    
    # asyncio.run(example())
