from typing import Union
from controllers.chatbot import th, my_local_tools, MODEL, client
import fastapi

app = fastapi.FastAPI()

@app.post("/message")
async def receive_message(message: str, latitude: float, longitude: float):
	# Process the message and coordinates here
	# return {"message": message, "latitude": latitude, "longitude": longitude}
	response = client.chat.completions.create(
		model=MODEL,
		messages=[{"role": "user", "content": message}],
		# Passes Code Execution as
		# a tool
		tools=th.get_tools() + my_local_tools,
	)

	# Runs the Code Execution tool, gets the result,
	# and appends it to the context
	tool_run = th.run_tools(response)

	# Appends the user message to the context
	messages = [{"role": "user", "content": message}]
	messages.extend(tool_run)

	response = client.chat.completions.create(
		model=MODEL,
		messages=messages,
		# tools=th.get_tools(),
	)
	return {"message": response.choices[0].message.content}


	# return {"message": message}


	# response = client.chat.completions.create(
	#     model=MODEL,
	#     messages=messages,
	#     # Passes Code Execution as a tool
	#     tools=th.get_tools() + my_local_tools,
	#     )

	# # Runs the Code Execution tool, gets the result, 
	# # and appends it to the context
	# tool_run = th.run_tools(response)
	# print(tool_run)
	# messages.extend(tool_run)

	# response = client.chat.completions.create(
	# model=MODEL,
	# messages=messages,
	# #   tools=th.get_tools(),
	# )

	# print(response.choices[0].message.content)

