from __future__ import annotations

import os
from dataclasses import dataclass

import openai
from openai import OpenAI

from .incidents import STATE


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass
class Response:
    text: str
    usage: Usage
    model: str


class OpenAILLM:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> Response:
        """Generate a response using OpenAI API."""
        try:
            # Simulate cost spike incident by using more expensive model
            model = "gpt-4o" if STATE["cost_spike"] else self.model
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Provide concise, accurate answers based on the context provided."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300,
            )
            
            message = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            
            return Response(
                text=message,
                usage=Usage(input_tokens=input_tokens, output_tokens=output_tokens),
                model=model
            )
        except openai.APIError as e:
            # Handle API errors
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            # Handle other errors
            raise RuntimeError(f"LLM generation failed: {str(e)}") from e
