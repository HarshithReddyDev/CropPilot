from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings

disease_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Plant Disease Specialist for CropPilot. Diagnose crop diseases "
     "from symptoms and provide treatment recommendations."),
    ("human", "{input}"),
])

disease_agent = disease_prompt | ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.3,
    api_key=settings.OPENAI_API_KEY,
)
