from typing import Any
import httpx
from datetime import datetime
import asyncio
import pytz


# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-hourly-update (chiaweh2@uci.edu)"  # NWS recommends including contact info
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
        "User-Agent": USER_AGENT,  # Required by NWS
        "Accept": "application/geo+json"  # NWS returns GeoJSON format
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
    generate_time = forecast_data["properties"]["generatedAt"]
    generate_time_mt = datetime.fromisoformat(generate_time).astimezone(pytz.timezone("America/Denver"))
    generate_time_formatted = generate_time_mt.strftime("%a %b %d, %I:%M %p MT")
    forecast_header = (
        f"Weather Forecast (Generated at {generate_time_formatted}):\n"
    )

    periods = forecast_data["properties"]["periods"]
    mountain_tz = pytz.timezone("America/Denver")
    current_time_mt = datetime.now(mountain_tz)
    
    # Find the current period based on Mountain Time
    current_period_index = 0
    for i, period in enumerate(periods):
        start_time = datetime.fromisoformat(period["startTime"])
        end_time = datetime.fromisoformat(period["endTime"])
        start_time_mt = start_time.astimezone(mountain_tz)
        end_time_mt = end_time.astimezone(mountain_tz)
        
        # Check if current time falls within this period
        if start_time_mt <= current_time_mt < end_time_mt:
            current_period_index = i
            break
        # If current time is before the first period, use the first period
        elif current_time_mt < start_time_mt:
            current_period_index = i
            break
    
    # Get current period and next 3 consecutive periods (4 total)
    selected_periods = periods[current_period_index:current_period_index + 4]
    
    forecasts = [forecast_header]
    for period in selected_periods:
        start_time = datetime.fromisoformat(period["startTime"])
        start_time_mt = start_time.astimezone(mountain_tz)
        start_time_formatted = start_time_mt.strftime("%a %b %d, %I:%M %p MT")

        end_time = datetime.fromisoformat(period["endTime"])
        end_time_mt = end_time.astimezone(mountain_tz)
        end_time_formatted = end_time_mt.strftime("%a %b %d, %I:%M %p MT")

        forecast = (
            f"{start_time_formatted} - {end_time_formatted}:\n"
            f"Temperature: {period['temperature']}°{period['temperatureUnit']}\n"
            f"Precipitation: {period['probabilityOfPrecipitation']['value']}%\n"
            f"Wind: {period['windSpeed']} {period['windDirection']}\n"
        )
        forecasts.append(forecast)

    return "\n===\n".join(forecasts)


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

