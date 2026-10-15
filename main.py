import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from database import seed_db
from graph import build_graph
from schemas import CustomerRequest, ReviewRequest

# Load environment variables from .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY missing. Please check your .env file."
        )

    seed_db()
    app.state.graph = build_graph(InMemorySaver())
    yield


app = FastAPI(
    title="LangGraph Refund Agent",
    description="AI-powered customer support and refund workflow",
    version="1.0.0",
    lifespan=lifespan,
)


# Serve frontend CSS and JavaScript.
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)


# Home page: serve the UI.
@app.get("/", include_in_schema=False)
def home():
    index_file = BASE_DIR / "templates" / "index.html"

    if not index_file.is_file():
        raise HTTPException(
            status_code=500,
            detail="UI file missing: templates/index.html",
        )

    return FileResponse(index_file)


def format_result(graph, thread_id, result):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)

    interrupts = [
        item.value for item in result.get("__interrupt__", ())
    ]

    return {
        "thread_id": thread_id,
        "status": (
            "awaiting_approval" if interrupts else "completed"
        ),
        "interrupts": interrupts,
        "decision": snapshot.values.get("decision"),
        "response": (
            snapshot.values.get("response")
            if not interrupts
            else None
        ),
    }


# Create a new customer support request.
@app.post("/support")
def support(body: CustomerRequest):
    graph = app.state.graph

    config = {
        "configurable": {"thread_id": body.thread_id}
    }

    existing = graph.get_state(config)

    if existing.values:
        raise HTTPException(
            status_code=409,
            detail=(
                "Thread already exists. "
                "Use a new thread_id for a new request."
            ),
        )

    result = graph.invoke(
        {
            "message": body.message,
            "request_id": str(uuid.uuid4()),
        },
        config=config,
    )

    return format_result(graph, body.thread_id, result)


# Approve or reject a request awaiting human review.
@app.post("/review/{thread_id}")
def review(thread_id: str, body: ReviewRequest):
    graph = app.state.graph

    config = {
        "configurable": {"thread_id": thread_id}
    }

    snapshot = graph.get_state(config)

    if not snapshot.next or "human_review" not in snapshot.next:
        raise HTTPException(
            status_code=409,
            detail="No pending human review for this thread.",
        )

    result = graph.invoke(
        Command(resume={"approved": body.approved}),
        config=config,
    )

    return format_result(graph, thread_id, result)


# Health check endpoint.
@app.get("/health")
def health():
    return {"status": "ok"}
