import openai
import requests
from env import OPENAI_API_KEY, ASSISTANT_ID, MCP_URL

openai.api_key = OPENAI_API_KEY

def run_mcp_conversation(message: str):
    thread = openai.beta.threads.create()

    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "completed":
            break

        elif run_status.status == "requires_action":
            tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
            args = eval(tool_call.function.arguments)
            mcp_response = requests.post(MCP_URL, json=args).json()

            openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=[{
                    "tool_call_id": tool_call.id,
                    "output": str(mcp_response)
                }]
            )

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value