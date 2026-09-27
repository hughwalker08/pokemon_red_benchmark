import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

JEV_MODEL = os.getenv("JEV_MODEL", "typesafe/jev-1.13")
JEV_ENDPOINT = os.getenv("JEV_ENDPOINT", "https://openrouter.ai/api/alpha/decisions")

SOL_MODEL = os.getenv("SOL_MODEL", "openai/gpt-6-sol")
SOL_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

GAME_SERVER = "http://localhost:8765"
