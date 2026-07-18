from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings

notif_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Notification Agent for CropPilot. Generate timely, relevant "
     "notifications for farmers about weather alerts, market prices, disease outbreaks, and scheme deadlines."),
    ("human", "{input}"),
])

notification_agent = notif_prompt | ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.2,
    api_key=settings.OPENAI_API_KEY,
)
