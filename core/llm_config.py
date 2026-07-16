import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

# Centraliza a inteligência do projeto
nexus_llm = LLM(
    model="openrouter/free",
    api_key=os.getenv("LLM_API_KEY"),
    temperature=0.2
)