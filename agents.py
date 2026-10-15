import os
import re
from langchain_groq import ChatGroq
from schemas import Classification


def llm():
    return ChatGroq(model=os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b'), temperature=0)


def classify(message: str) -> dict:
    result = llm().with_structured_output(Classification).invoke([
        ('system', 'Classify the customer support request. Extract an order ID like ORD-1001 if present. Never invent an ID.'),
        ('human', message),
    ])
    # Deterministic regex avoids losing an explicit ID to model formatting.
    match = re.search(r'\bORD-\d+\b', message, re.IGNORECASE)
    return {'intent': result.intent, 'order_id': match.group(0).upper() if match else result.order_id}


def compose_reply(message: str, outcome: str, detail: str) -> str:
    response = llm().invoke([
        ('system', 'Write a concise, courteous customer service reply. The outcome and detail are authoritative. Never say a payment was sent or money returned when only a demo ledger was updated. Never override the decision.'),
        ('human', f'Customer: {message}\nOutcome: {outcome}\nDetail: {detail}'),
    ])
    return response.content if isinstance(response.content, str) else str(response.content)
