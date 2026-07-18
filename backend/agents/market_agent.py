from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings

market_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Market Intelligence Agent for CropPilot. Analyze agricultural "
     "commodity prices, trends, and help farmers make informed selling decisions."),
    ("human", "{input}"),
])

market_agent = market_prompt | ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.2,
    api_key=settings.OPENAI_API_KEY,
)
