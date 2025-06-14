@app.post("/bridge")
async def bridge_to_scribe(request: Request):
    body = await request.json()
    user_input = body.get("message", "Hello")

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "completed":
            break

        elif run_status.status == "requires_action":
            tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
            args = eval(tool_call.function.arguments)
            mcp_response = requests.post(MCP_URL, json=args).json()

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=[{
                    "tool_call_id": tool_call.id,
                    "output": str(mcp_response)
                }]
            )

    messages = client.beta.threads.messages.list(thread_id=thread.id)

    if messages.data and messages.data[0].content:
        return {"response": messages.data[0].content[0].text.value}
    else:
        return {"response": f"✅ Tool executed. MCP response: {mcp_response}"}
