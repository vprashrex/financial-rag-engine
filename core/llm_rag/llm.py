import os
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
from google import genai
from google.genai import types
from logger import llm_logger as logger
from memory.conv_memory import save_message_memory, load_context
from core.llm_rag.prompt import prompt_template
from core.AgentTool.func_tool import finacial_agent

load_dotenv()


class GenaiChat:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash-preview-05-20")

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    async def create_chat_completion(self, contents):
        """
        Create a chat completion using Google GenAI API.

        Args:
            contents: List of Content objects for the conversation

        Returns:
            The response from the Google GenAI API.
        """
        try:
            config = types.GenerateContentConfig(response_mime_type="text/plain")
            response = await self.client.aio.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error creating chat completion: {str(e)}")
            raise

    async def generate_user_content(self, user_query: str, chat_id: str):
        """
        Generate user content for the chat.

        Args:
            user_query (str): The user's query.
            chat_id (str): The ID of the chat.

        Returns:
            Content object containing the user's query.
        """

        # retrieve the context from the vectordb
        # context = vectordb stock market data + finacial document market data
        context = await finacial_agent(query=user_query, chat_id=chat_id)

        # Load chat history from memory
        chat_history = await load_context(chat_id=chat_id)

        # Create the user content with the prompt template
        chat_input = prompt_template.format(
            chat_history=chat_history,
            query=user_query,
            market_query_result=context.get("market_query_result", "No relevant financial data found."),
            document_query_result=context.get("document_query_result", "No relevant documents found.")
        )

        # Create and return the Content object for the user query
        content = [
            types.Content(role="user", parts=[types.Part.from_text(text=chat_input)])
        ]

        return content

    async def generate(self, query: str, chat_id: str):
        """
        Generate a response based on the user's query.

        Args:
            query (str): The user's query.
            chat_id (str): The ID of the chat.

        Returns:
            The generated response from the Google GenAI API.
        """
        try:
            contents = await self.generate_user_content(query, chat_id)

            # Create the chat completion
            response = await self.create_chat_completion(contents)

            # save the user query and response to memory
            await save_message_memory(chat_id=chat_id, content=query, role="user")
            await save_message_memory(
                chat_id=chat_id, content=response, role="assistant"
            )

            return response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
