import os
from typing import TypedDict
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END

import os
from dotenv import load_dotenv

# This is the line you are missing!
load_dotenv()

# Now you can check if it's actually there
if not os.getenv("ANTHROPIC_API_KEY"):
    print("API Key not found! Check your .env file.")
else:
    print("API Key loaded successfully.")

# 1. Initialize Claude
llm = ChatAnthropic(model="claude-3-5-haiku-20241022", temperature=0)


# 2. Define the State
class AgentState(TypedDict):
    code: str
    error_log: str
    iterations: int


def explorer_node(state: AgentState):
    """Understands the codebase based on the issue"""

    prompt = f"""
    I need to work on this issue: {state['issue_description']}
    
    Project structure:
    {get_project_tree()}
    
    Which files are most relevant? What do I need to understand?
    """

    response = llm.invoke(prompt)

    # Agent decides which files to read
    relevant_files = parse_files_from_response(response)

    # Read those files into context
    codebase_context = {}
    for file in relevant_files:
        codebase_context[file] = read_file(file)

    return {"codebase_context": codebase_context}


# 3. The Coder Node
def coder_node(state: AgentState):
    print(f"--- CODER (Iteration {state['iterations']}) ---")

    prompt = f"""
    You are an expert Python developer. 
    Fix the bug in the following code based on the error log.
    
    CODE:
    {state['code']}
    
    ERROR:
    {state['error_log']}
    
    Return ONLY the corrected code. No explanations.
    """

    response = llm.invoke(
        prompt,
    )
    new_code = response.content

    # Update our sandbox file
    with open("sandbox_code.py", "w") as f:
        f.write(new_code)

    return {"code": new_code, "iterations": state["iterations"] + 1}


# 4. The Tester Node (The one we built earlier)
import subprocess


def tester_node(state: AgentState):
    print("--- TESTING ---")
    result = subprocess.run(
        ["pytest", "test_sandbox.py"], capture_output=True, text=True
    )

    return {
        "test_results": "PASSED" if result.returncode == 0 else "FAILED",
        "error_log": result.stdout + result.stderr,
    }


# 5. Routing Logic
def should_continue(state: AgentState):
    if "PASSED" in state.get("test_results", ""):
        return "end"
    if state["iterations"] >= 3:
        print("Max iterations reached!")
        return "end"
    return "fix"


# 6. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("coder", coder_node)
workflow.add_node("tester", tester_node)

workflow.set_entry_point("coder")
workflow.add_edge("coder", "tester")
workflow.add_conditional_edges("tester", should_continue, {"fix": "coder", "end": END})

app = workflow.compile()

initial_state = {
    "issue_description": "User reports that result is a multiplaction not sum",
    "issue_url": "https://github.com/user/repo/issues/123",
    "codebase_context": {},
}

app.invoke(initial_state)
