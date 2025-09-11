from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from datetime import datetime
import requests
import asyncio
import os

load_dotenv()

weather_api_key = os.getenv("WEATHER_API_KEY")

mcp = FastMCP("Custom MCP Server", "A custom MCP server with a custom tool.")

@mcp.tool(
    name = "get_date_time",
    title = "Get Current Date and Time",
    description = "Returns the current date and time in YYYY-MM-DD HH:MM:SS format."
)
def get_date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool(
    name = "weather_info",
    title = "Get Weather Information",
    description = "Fetches current weather information for a given location using OpenWeatherMap API."
)
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

@mcp.tool(
    name = "get_book",
    title = "Get Book Information",
    description = "Fetches book information from Google Books API based on the book name."
)
def get_book(book_name: str) -> str:
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": book_name,
        "maxResults": 1
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return f"Error: {response.status_code}"
 
    data = response.json()
 
    if "items" not in data:
        print("No books found.")
        return "No books found."
 
    for index, item in enumerate(data["items"], start=1):
        volume_info = item.get("volumeInfo", {})
        title = volume_info.get("title", "N/A")
        authors = ", ".join(volume_info.get("authors", ["Unknown author"]))
        publisher = volume_info.get("publisher", "N/A")
        return (f"\nBook {index}: Title: {title} Authors: {authors} Publisher: {publisher}")

@mcp.tool(
    name = "ddg_search",
    title = "DuckDuckGo Search",
    description = "Performs a web search using DuckDuckGo's Instant and current Answer API."
)
def ddg_search(query: str, max_results: int = 5) -> str:
    """
    Performs a web search using DuckDuckGo's Instant Answer API.
    Returns a formatted string of instant answer or top related topics.
    """ 
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
    resp = requests.get("https://api.duckduckgo.com/", params=params)
    resp.raise_for_status()
    data = resp.json()

    abstract = data.get("AbstractText") 
    citation = data.get("AbstractURL") 
    results = []
    
    if 'Text' in data and 'FirstURL' in data:
        results.append(f"- {data['Text']}: {data['FirstURL']}")

    output = ""
    if abstract:
        output += f"**Instant Answer:** {abstract}\n\n"
    if abstract:
        output += f"**citation:** {citation}\n"  
    return output or "No results found."

async def main():
    await mcp.run_streamable_http_async()

if __name__ == "__main__":
    asyncio.run(main())

# python MCP_custom_server.py 