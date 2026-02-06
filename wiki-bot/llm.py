from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langsmith import traceable
from config import MODEL_NAME
from logger import log_node

# Initialize shared instances
openai_client = ChatOpenAI(model=MODEL_NAME, temperature=0)
embeddings = OpenAIEmbeddings()


@traceable(run_type="llm")
def call_llm(node_name: str, system_prompt: str, prompt: str):
    # log_node(
    #     node_name,
    #     {"message": f"Calling LLM with prompt: {prompt}"},
    # )

    response = openai_client.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
    )

    # log_node(
    #     node_name,
    #     {"message": f"LLM response: {response.content}"},
    # )
    return response.content
