"""
# This file defines the tools that can be used by the agent.
# It includes a financial agent tool that can be invoked when the user asks for financial information.
"""
from google.genai import types

gemini_tools = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="finacial_agent",
                description="This tool should be invoked when the user asks for financial information.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING,
                        ),
                    },
                    required=["query"],
                ),
            )
        ]
    )
]