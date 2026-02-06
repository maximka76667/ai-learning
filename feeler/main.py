# State
# my feeling

# Nodes
# 1. the one that reads what i wrote and interprets it
# 2. node that gives me some encouragement

# Graph
# receive input -> interpret -> give encouragement -> output

import json
import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, StateGraph

# This is the line you are missing!
load_dotenv()

# Now you can check if it's actually there
if not os.getenv("ANTHROPIC_API_KEY"):
    print("API Key not found! Check your .env file.")
else:
    print("API Key loaded successfully.")

# 1. Initialize Claude
llm = ChatAnthropic(model="claude-3-5-haiku-20241022", temperature=0)


class State(TypedDict):
    user_input: str
    interpretation: str
    encouragement: str  # Temporary encouragement (changes each iteration)
    final_output: str  # Only set when quality is good
    good_score: float
    suitable_score: float
    iterations: int
    improvements: list[str]


def interpret_node(state: State):
    prompt = f"""
    You are a helpful assistant that interprets user input.
    User input: {state['user_input']}
    Interpret the user input and return a short summary.
    Maybe what does it mean? Or what kind of help would person need?
    Also you get improvements from reflection node. You should use them to improve your interpretation.
    Improvements: {state.get('improvements', [])} if it's empty then ignore it
    """
    interpretation = llm.invoke(prompt)
    print(interpretation.content)
    return {
        "interpretation": interpretation.content,
        "iterations": state.get("iterations", 0) + 1,
    }


def encouragement_node(state: State):
    prompt = f"""
    You are a helpful assistant that gives encouragement. You get interpretation of user input and his feeling.
    You need to give the person some encouragement based on the interpretation and his feeling.
    Interpretation: {state['interpretation']}
    Give the person some encouragement. I don't want it to be too long. Also i dont want some cliche answer mybe something funny could work, like something abstract
    or something that doesnt make sense but is funny.
    """
    encouragement = llm.invoke(prompt)
    print(encouragement.content)
    return {"encouragement": encouragement.content}  # Changed from "output"


def judge_node(state: State):
    prompt = f"""
    You are a judge node, previous node gave user an encouragement phrase.
    You should evaluate it from 0 to 1 how good it is and how suitable it is.

    Encouragement: {state['encouragement']}  # Changed from state['output']

    Return ONLY valid JSON without any other text like:
    good_score: float between 0 and 1
    suitable_score: float between 0 and 1
    """
    score = llm.invoke(prompt)
    print(score.content)

    score_dict = json.loads(score.content)

    return {
        "good_score": float(score_dict["good_score"]),
        "suitable_score": float(score_dict["suitable_score"]),
    }


def conditional_node(state: State):
    print(state)
    if (
        state["good_score"] > 0.9
        and state["suitable_score"] > 0.9
        or state["iterations"] > 2
    ):
        return "end"
    else:
        return "repeat"


def reflection_node(state: State):
    prompt = f"""
    you are an assistant that helps improve my api's response for encouragement.
    you recieve evalutation from judge node scores. i want you to write 1-2 improvements that could
    improve score of a message.
    
    Evaluation: How good it is score: {state['good_score']} and how suitable it is score: {state['suitable_score']}
    """

    reflection = llm.invoke(prompt)
    print(reflection.content)
    return {"improvements": state.get("improvements", []) + [reflection.content]}


def finalize_node(state: State):
    """Sets the final output when quality is good"""
    return {"final_output": state["encouragement"]}


workflow = StateGraph(State)
workflow.add_node("interpret", interpret_node)
workflow.add_node("encouragement", encouragement_node)
workflow.add_node("judge", judge_node)
workflow.add_node("reflection", reflection_node)
workflow.add_node("finalize", finalize_node)  # New node

workflow.set_entry_point("interpret")
workflow.add_edge("interpret", "encouragement")
workflow.add_edge("encouragement", "judge")
workflow.add_edge("reflection", "interpret")

workflow.add_conditional_edges(
    "judge",
    conditional_node,
    {
        "end": "finalize",  # When good, go to finalize
        "repeat": "reflection",  # When bad, reflect and try again
    },
)

workflow.add_edge("finalize", END)  # After finalize, end

app = workflow.compile()
