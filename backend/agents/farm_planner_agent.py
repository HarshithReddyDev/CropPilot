from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Farm Planning Agent for CropPilot. Help farmers plan their "
     "cropping cycles, rotations, and resource allocation for maximum yield and profitability."),
    ("human", "{input}"),
])

farm_planner_agent = planner_prompt | ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.3,
    api_key=settings.OPENAI_API_KEY,
)
