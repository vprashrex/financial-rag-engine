import os
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
from google import genai
from google.genai import types
from logger import llm_logger as logger
from memory.conv_memory import save_message_memory, load_context
import json
from core.AgentTool.func_tool import function_definations
from core.AgentTool.tool_defination import gemini_tools
from core.llm_rag_agent.prompt import (
    prompt_template,
    prompt_rag
)

load_dotenv()


class GenaiChat:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash-preview-05-20")

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    async def create_chat_completion(self, contents, **kwargs):
        """
        Create a chat completion using Google GenAI API.

        Args:
            contents: List of Content objects for the conversation
            tools: Tools to use for function calling

        Returns:
            The response from the Google GenAI API.
        """
        try:

            response = await self.client.aio.models.generate_content(
                model=self.model_name, contents=contents, **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Error creating chat completion: {str(e)}")
            raise

    async def call_function(
        self, function_calls_part, function_call_content, user_query: str, chat_id: str
    ):
        """
        Call functions from GenAI function calls

        Args:
            function_calls: Function calls from GenAI response
            functions: Dictionary of available functions
            **kwargs: Additional arguments

        Returns:
            Result of the function call
        """
        try:
            # Implemented single function call handling for simplicity
            func_call = function_calls_part[0]
            # Extract function name and arguments
            function_name = func_call.name
            function_args = func_call.args
            function_args.update({"chat_id": chat_id})

            func = function_definations[function_name]
            function_result = await func(**function_args)
            logger.info(f"Calling function: {function_name} with args: {function_args}")
            logger.info(f"Function result: {function_result}")

            function_response_part = types.Part.from_function_response(
                name=function_name, response={"result": function_result}
            )

            function_response_content = types.Content(
                role="tool", parts=[function_response_part]
            )

            config = types.GenerateContentConfig(response_mime_type="text/plain")
            user_prompt_query = types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt_rag.format(query=user_query))
                ]
            )
            response = await self.create_chat_completion(
                contents=[
                    user_prompt_query,
                    function_call_content,
                    function_response_content,
                ],
                config=config,
            )

            return response.text

        except Exception as e:
            logger.error(f"Error calling function: {str(e)}")
            raise

    async def generate_user_content(
        self, chat_id: str, user_query: str
    ):
        chat_history = await load_context(chat_id)
        chat_input = prompt_template.format(
            chat_history=chat_history,
            query=user_query,
        )
        print(f"Chat input for chat_id {chat_id}: \n\n{chat_input}")
        content = [
            types.Content(role="user", parts=[types.Part.from_text(text=chat_input)])
        ]

        return content

    async def generate(self, query: str, chat_id: str):
        """
        Generate a response based on the user's query.

        Args:
            query: The user's query.
            chat_id: The ID of the chat.

        Returns:
            The generated response from the Google GenAI API.
        """
        try:
            contents = await self.generate_user_content(chat_id, query)

            config = types.GenerateContentConfig(
                response_mime_type="text/plain",
                tools=gemini_tools,
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(mode="AUTO")
                ),
            )
            response = await self.create_chat_completion(
                contents=contents, config=config
            )
            

            # function call handling
            function_call_part = response.function_calls
            
            if function_call_part:
                function_call_content = response.candidates[0].content
                logger.info(f"Function call detected: {function_call_part}")
                response_text = await self.call_function(
                    function_call_part, function_call_content, query, chat_id
                )
                await save_message_memory(chat_id, content=query, role="user")
                await save_message_memory(chat_id, content=response_text, role="model")
                return response_text
            else:
                result = response.text
                await save_message_memory(chat_id, content=query, role="user")
                await save_message_memory(chat_id, content=result, role="model")
                return result

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
