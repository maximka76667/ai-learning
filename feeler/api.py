import json
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from feeler.main import app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

api = FastAPI(title="Feeling Interpreter API")


# Request/Response models
class FeelingRequest(BaseModel):
    user_input: str


class FeelingResponse(BaseModel):
    output: str


api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/")
async def get_health():
    return {"status": "ok"}


@api.get("/stream")
async def stream_feeling(user_input: str):
    async def generate():
        try:
            final_state = None  # Store the final state

            for event in app.stream(
                {"user_input": user_input, "iterations": 0, "improvements": []}
            ):
                node_name = list(event.keys())[0]
                node_data = event[node_name]
                final_state = event  # Keep updating with latest state

                if node_name == "interpret":
                    yield f"data: {json.dumps({'status': 'interpreting', 'message': '🤔 Analyzing your feeling...'})}\n\n"
                elif node_name == "encouragement":
                    yield f"data: {json.dumps({'status': 'encouraging', 'message': '💪 Generating encouragement...'})}\n\n"
                elif node_name == "judge":
                    yield f"data: {json.dumps({'status': 'judging', 'message': '⚖️ Evaluating quality...'})}\n\n"
                elif node_name == "reflection":
                    yield f"data: {json.dumps({'status': 'reflecting', 'message': '🔄 Reflecting on previous attempt...'})}\n\n"
                elif node_name == "finalize":
                    # When finalize runs, we know we have the good output
                    final_output = node_data.get("final_output")
                    yield f"data: {json.dumps({'status': 'complete', 'message': '✅ Done!', 'data': {'output': final_output}})}\n\n"
                    return  # End here

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': f'❌ Error: {str(e)}'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host="0.0.0.0", port=8000)
