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

GDEX_MCP_SERVER_URL = os.getenv("GDEX_MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")

logging.basicConfig(
    format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("kernel").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# ----------------------------- kernel & services -----------------------------
conversation_id = "convo-914"
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
    instructions="Be a helpful assistant that helps the user with their queries.",
    )

# ----------------------------- helpers -----------------------------
def _to_author_role(role_str: str) -> AuthorRole:
    r = (role_str or "").lower()
    if r == "user":
        return AuthorRole.USER
    if r in ("assistant", "assistant_model", "bot"):
        return AuthorRole.ASSISTANT
    if r == "system":
        return AuthorRole.SYSTEM
    if r in ("tool", "function"):
        return AuthorRole.TOOL
    return AuthorRole.USER

def _coerce_content_to_str(content) -> str:
    if isinstance(content, (dict, list)):
        return json.dumps(content, ensure_ascii=False)
    return str(content) if content is not None else ""

# ----------------------------- main loop -----------------------------
async def main():
    contact_id = os.getenv("CONTACT_ID")

    async with MCPStreamableHttpPlugin(
        name="gdexmcpserver",
        description="MCP plugin for GDex using streaming",
        url=GDEX_MCP_SERVER_URL,
        load_prompts=False,
        request_timeout=30,
    ) as gdex_plugin:
        kernel.add_plugin(gdex_plugin)
        logger.info(f"MCP plugin connected successfully to {GDEX_MCP_SERVER_URL}")

        while True:
            query = input("User: ")
            if query.lower().strip() == "exit":
                break

            sk_history.add_user_message(query)

            start = time.time()

            try:
                # run assistant and capture output
                response = await agent.get_response(sk_history)
                assistant_text = response.message.content if response else ""
                print(f"Assistant: {assistant_text}")

            except Exception as e:
                logger.exception("Error during agent completion: %s", e)

            end = time.time()
            print(f"Response Time: {end - start:.2f} seconds")
            print("-" * 120)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "asyncio.run()" in str(e) or "already running" in str(e).lower():
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise