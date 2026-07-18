from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings

finance_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Finance Agent for CropPilot. Help farmers with financial planning, "
     "loan applications, subsidy calculations, and profitability analysis."),
    ("human", "{input}"),
])

finance_agent = finance_prompt | ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.2,
    api_key=settings.OPENAI_API_KEY,
)
