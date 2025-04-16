from os import getenv
from llama_index.llms.openrouter import OpenRouter
from llama_index.core import Settings
from .logic import BM25, chat_query_engine
import asyncio

Settings.llm = OpenRouter(
    api_key=getenv("OPEN_ROUTER_TOKEN"),
    max_tokens=256,
    context_window=4096,
    model="meta-llama/llama-3.1-8b-instruct:free",
    # model="google/gemini-flash-1.5-exp",
)

query_engine = asyncio.run(BM25())

chat_query_engine = chat_query_engine()
