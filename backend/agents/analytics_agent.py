from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings

analytics_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an Analytics Agent for CropPilot. Analyze farm data, detect patterns, "
     "and provide data-driven insights for better decision making."),
    ("human", "{input}"),
])

analytics_agent = analytics_prompt | ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.2,
    api_key=settings.OPENAI_API_KEY,
)
