from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings

weather_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Weather Agent for CropPilot. Analyze weather data and provide "
     "agricultural recommendations based on current and forecasted conditions."),
    ("human", "{input}"),
])

weather_agent = weather_prompt | ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.2,
    api_key=settings.OPENAI_API_KEY,
)
