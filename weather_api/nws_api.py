from typing import Any
import httpx
from datetime import datetime
import asyncio


# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"
BOULDER_POINTS = [40.01,-105.27] # lat, lon for Boulder, CO
# Example URLs:
# https://api.weather.gov/points/40.01,-105.27
# https://api.weather.gov/gridpoints/BOU/54,74/forecast/hourly

async def make_nws_request(url: str) -> dict[str, Any] :
    """
    Make an asynchronous HTTP GET request to the NWS API with error handling.

    Parameters
    ----------
    url : str
        The URL endpoint of the NWS API to request data from.
    
    Returns
    -------
    dict[str, Any]
        The JSON response from the NWS API parsed as a dictionary.
    
    Raises
    ------
    RuntimeError
        If the request fails or the response status is not successful.
    
    Notes
    -----
    The request includes a custom User-Agent and expects a response in GeoJSON format.
    
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from NWS API: {e}")


async def get_forecast(latitude: float, longitude: float) -> str:
    """
    Get weather forecast for a location.
    Using two API calls:
    1. Get the forecast grid endpoint using latitude and longitude.
    2. Fetch the detailed forecast from the grid endpoint.

    Parameters
    ----------
    latitude : float
        Latitude of the location.
    longitude : float
        Longitude of the location.

    """
    # API call 1. Get the forecast URL from the points response
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        raise RuntimeError("Unable to fetch points data from NWS API.")

    # API call 2. Get the detailed forecast from the grid endpoint
    forecast_url = points_data["properties"]["forecastHourly"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        raise RuntimeError("Unable to fetch detailed forecast.")

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:4]:  # Only show next 4 periods
        # Parse the ISO datetime string and format it nicely
        start_time = datetime.fromisoformat(period["startTime"])
        start_time_formatted = start_time.strftime("%a %b %d, %I:%M %p")

        end_time = datetime.fromisoformat(period["endTime"])
        end_time_formatted = end_time.strftime("%a %b %d, %I:%M %p")

        forecast = (
            f"{start_time_formatted} - {end_time_formatted}:\n"
            f"Temperature: {period['temperature']}°{period['temperatureUnit']}\n"
            f"Wind: {period['windSpeed']} {period['windDirection']}\n"
        )
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


async def main():
    """
    Main function to get and display weather forecast.
    """
    try:
        # Use Boulder, CO coordinates as default
        latitude, longitude = BOULDER_POINTS
        
        print(f"Fetching weather forecast for Boulder, CO ({latitude}, {longitude})...")
        print("=" * 60)
        
        # Get the forecast
        forecast = await get_forecast(latitude, longitude)
        
        # Output the forecast
        print(forecast)
        print("=" * 60)
        print("Weather forecast completed successfully!")
        
    except Exception as e:
        print(f"Error fetching weather forecast: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

