import logging
import os
import uuid
import asyncio
import semantic_kernel as sk
from datetime import datetime, timezone
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory

# The following lines are for local development.
# from dotenv import load_dotenv
# load_dotenv()

# Load environment variables
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "")
COSMOS_DATABASE_NAME = os.getenv("COSMOS_DATABASE_NAME", "")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME", "")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")

# Initialize CosmosDB client
_cosmos_client = None
try:
    credential = DefaultAzureCredential()
    _cosmos_client = CosmosClient(COSMOS_ENDPOINT, credential)
except Exception as e:
    logging.error(f"Failed to connect to CosmosDB with Managed Identity: {e}")

if not _cosmos_client:
    logging.error("Failed to initialize CosmosDB client. Please check your environment variables.")
    raise RuntimeError("Failed to initialize CosmosDB client.")

_database = _cosmos_client.get_database_client(COSMOS_DATABASE_NAME)
_container = _database.get_container_client(COSMOS_CONTAINER_NAME)

# Initialize Semantic Kernel
kernel = sk.Kernel()
chat_service = AzureChatCompletion(
    deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
    endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)
kernel.add_service(chat_service)

async def process_request(session: str, user_msg: str) -> str:
    """Process user request and return response from Azure OpenAI."""
    try:
        # Get chat history
        chat = ChatHistory()
        # Get messages related to the session from CosmosDB
        items = _container.query_items(
            query=f"SELECT * FROM c WHERE c.sessionid='{session}'",
            enable_cross_partition_query=True,
        )

        # Add messages from CosmosDB to chat history
        for item in items:
            role = item.get("role")
            message = item.get("message", "")

            if role == "user":
                chat.add_user_message(message)
            elif role == "assistant":
                chat.add_assistant_message(message)


        # Add user message to chat history
        chat.add_user_message(user_msg)
        save_message_to_cosmosdb(session, user_msg, "user")

        # Get response from Azure OpenAI
        chat_completion_service = kernel.get_service(type=AzureChatCompletion)
        response = await chat_completion_service.get_chat_message_contents(
            chat_history=chat,
            settings=chat_completion_service.get_prompt_execution_settings_class()(
                max_tokens=1000, temperature=0.7
            ),
        )

        # Extract response message
        answer = response[0].content if response else "No response generated."

        # Save response to CosmosDB
        save_message_to_cosmosdb(session, answer, "assistant")

        return answer
    except Exception as e:
        logging.error(f"An error occurred while processing the request: {e}")
        raise

def save_message_to_cosmosdb(session: str, message: str, role: str):
    """Helper function to save messages to CosmosDB."""
    _container.create_item(
        {
            "id": str(uuid.uuid4()),
            "sessionid": session,
            "message": message,
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

# Testing Purpose: Entry point to run the process_request function directly
if __name__ == "__main__":
    async def main():
        session_id = str(uuid.uuid4())
        user_message = "Hello, how can I add a new conversation history to Azure Cosmos DB?"
        try:
            response = await process_request(session_id, user_message)
            print(f"Response: {response}")
        except Exception as e:
            logging.error(f"Error: {e}")

    asyncio.run(main())
