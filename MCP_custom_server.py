from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from datetime import datetime
import requests
import asyncio
import os
load_dotenv()

weather_api_key = os.getenv("WEATHER_API_KEY")

mcp = FastMCP("Custom MCP Server", "A custom MCP server with a custom tool.")

@mcp.tool()
def get_date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
def weather_info(location: str) -> str:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={weather_api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        return f"The current weather in {location} is {weather} with a temperature of {temperature}°C."
    else:
        return f"The current weather of {location} is unavailable."

@mcp.tool()
def get_book(book_name: str) -> str:
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": book_name,
        "maxResults": 1
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
 
    data = response.json()
 
    if "items" not in data:
        print("No books found.")
        return
 
    for index, item in enumerate(data["items"], start=1):
        volume_info = item.get("volumeInfo", {})
        title = volume_info.get("title", "N/A")
        authors = ", ".join(volume_info.get("authors", ["Unknown author"]))
        publisher = volume_info.get("publisher", "N/A")
        return (f"\nBook {index}: Title: {title} Authors: {authors} Publisher: {publisher}")
 
async def main():
    await mcp.run_streamable_http_async()

if __name__ == "__main__":
    asyncio.run(main())

# python MCP_custom_server.py 