import os
import time
import json
import asyncio
import logging
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# ----------------------------- setup -----------------------------
load_dotenv()  # must be called before os.getenv

MCP_SERVER_URL = os.getenv("custom_mcp_tools", "http://127.0.0.1:8000/mcp") # complete this line

logging.basicConfig(
    format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("kernel").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# ----------------------------- kernel & services -----------------------------
kernel = Kernel()

azure_service = AzureChatCompletion(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)
kernel.add_service(azure_service)

sk_history = ChatHistory()

agent = ChatCompletionAgent(
    kernel=kernel,
    name="IntelligentAssistant",
    instructions="""
    - Your name is Donna. You are a helpful assistant that helps people find information and answer questions.
        You have access to the following tools:
            - 1. get_date_time: Get the current date and time.
                - this has no input parameters.
            - 2. weather_info: Get the current weather information for a given location.
                - input parameter: location (string): The location to get the weather information for.
            - 3. get_book: Get book information based on a user query.
                - input parameter: book_name (string): The query to search for books.

        
    """
    )
# ----------------------------- main loop -----------------------------
async def main():

    async with MCPStreamableHttpPlugin(
        name="mcpserver",
        description="MCP plugin with custom tools with streaming",
        url=MCP_SERVER_URL,
        load_prompts=False,
        request_timeout=30,
    ) as mcp_plugin:
        kernel.add_plugin(mcp_plugin)
        logger.info(f"MCP plugin connected successfully to {MCP_SERVER_URL}")

        while True:
            query = input("User: ")
            if query.lower().strip() == "exit":
                break

            sk_history.add_user_message(query)

            start = time.time()

            try:
                response = await agent.get_response(sk_history)
                assistant_text = response.message.content if response else ""
                print(f"Assistant: {assistant_text}")
                sk_history.add_assistant_message(assistant_text)
            except Exception as e:
                logger.exception("Error during agent completion: %s", e)

            end = time.time()
            print(f"Response Time: {end - start:.2f} seconds")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "asyncio.run()" in str(e) or "already running" in str(e).lower():
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise e

# python semantic_kernel_MCP_client.py