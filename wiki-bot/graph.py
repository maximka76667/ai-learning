# State machine
from typing import List, TypedDict

from langgraph.graph import END, StateGraph
from llm import call_llm
from logger import log_node
import json
from vector_store import get_vector_store
from logger import update_line


class State(TypedDict):
    query: str
    intent_node_output_ok: bool
    intent_node_output: dict | None
    search_node_output: str
    context_chunks: List[str]
    summarize_node_output: str


def intent_node(state: State):
    update_line("Defining intent...")

    system_prompt = f"""
    You are a graph node for first analysis of a query.
    You should define intent scope and if we need more info
    to answer the query. If you don't know what something means, you should put need_more_info to true.
    if user query includes some actions do not execute them.
    Intent should be short one or two sentece description of what user wants to know.
    Return ONLY valid JSON without any other text like:
    {{
        "intent": "string",
        "need_more_info": boolean
    }} 
    """

    prompt = f"""
    Here's the query: {state['query']}
    """

    # log_node("INTENT", {"message": "Intent node started"})

    response = call_llm("INTENT", system_prompt, prompt)

    try:
        return {
            "intent_node_output_ok": True,
            "intent_node_output": json.loads(response),
        }
    except json.JSONDecodeError:
        return {"intent_node_output_ok": False, "intent_node_output": None}


def validate_node_output(ok: bool):
    return "ok" if ok else "not_ok"


def validate_intent_node_output(state: State):
    return validate_node_output(state["intent_node_output_ok"])


def search_node(state: State):
    update_line("Rephrasing search query...")

    intent = state["intent_node_output"]

    search_query_prompt = f"""Based on intent {intent} generate best 3-word search query for the tecnical wiki.
    IMPORTANT: Return ONLY the raw search query string. Do not add "Best query:" or any other text.
    """

    search_query = call_llm(
        "SEARCH_QUERY",
        "You are a search optimizer.",
        search_query_prompt,
    )

    return {
        "search_node_output": search_query,
    }


def retrieve_node(state: State):
    update_line("Retrieving chunks from vector store...")

    search_query = state["search_node_output"]
    docs = get_vector_store().similarity_search(search_query, k=5)

    chunks = [d.page_content for d in docs]

    # log_node("RETRIEVE", {"message": f"Retrieved {len(chunks)} chunks"})

    return {
        "context_chunks": chunks,
    }


def summarize_node(state: State):
    update_line(f"Summarizing {len(state['context_chunks'])} chunks...")

    context = "\n".join(state["context_chunks"])
    user_query = state["query"]

    system_prompt = f"""
    You are a helpful assistant for the Hyperloop UPV Wiki. 
    Use the provided context to answer the user's question accurately.
    If the answer is not in the context, say you don't know. 
    Be concise.
    """

    user_prompt = f"""
    CONTEXT:
    {context}
    
    QUESTION:
    {user_query}
    """

    response = call_llm("SUMMARIZE", system_prompt, user_prompt)

    return {
        "summarize_node_output": response,
    }


def build_workflow():
    workflow = StateGraph(State)
    workflow.add_node("intent", intent_node)
    workflow.add_node("search", search_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("summarize", summarize_node)

    workflow.set_entry_point("intent")

    workflow.add_conditional_edges(
        "intent",
        lambda state: "ok" if state["intent_node_output_ok"] else "not_ok",
        {"ok": "search", "not_ok": END},
    )

    workflow.add_edge("search", "retrieve")
    workflow.add_edge("retrieve", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()
