from langchain_openai import ChatOpenAI

from app.model.contact_classification import ContactClassification
from app.prompt.contact_msg_classification import CLASSIFICATION_PROMPT

classification_model = ChatOpenAI(model="gpt-4.1-2025-04-14").with_structured_output(ContactClassification)

contact_classification_chain = CLASSIFICATION_PROMPT | classification_model


