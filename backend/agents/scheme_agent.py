from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings

scheme_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Government Scheme Advisor for CropPilot. Help farmers find and "
     "apply for relevant agricultural schemes and subsidies."),
    ("human", "{input}"),
])

scheme_agent = scheme_prompt | ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.2,
    api_key=settings.OPENAI_API_KEY,
)
