from typing import Union
from controllers.chatbot import th, my_local_tools, MODEL, client
from lib.mongo import retrieve_product_by_id, get_user_chat, upsert_user_chat
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class bodyMessage(BaseModel): 
	message: str
	latitude: float
	longitude: float
	userId: str

app = fastapi.FastAPI()

origins = [
    "http://localhost:3000",  # If running your frontend locally
    "https://hacking-the-list.vercel.app/",  # Your deployed frontend domain
]

user_map = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # 
)

@app.post("/message")
async def receive_message(body: bodyMessage):
	# Process the message and coordinates here
	# return {"message": message, "latitude": latitude, "longitude": longitude}
	message = body.message
	latitude = body.latitude
	longitude = body.longitude
	user = body.userId

	chat = get_user_chat(user)
	print(chat)
	if chat:
		messages = chat["chat"]
	else:
		messages = []

	# print(messages)
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
	print(tool_run)
	# Appends the user message to the context
	# messages = [{"role": "user", "content": message}]
	messages.append({"role": "user", "content": message})
	messages.extend(tool_run)

	response = client.chat.completions.create(
		model=MODEL,
		messages=messages,
		# tools=th.get_tools(),
	)
	messages.append( {"role": "assistant", "content": response.choices[0].message.content})
	upsert_user_chat(messages, user)

	return {"message": response.choices[0].message.content}

@app.get("/product/{product_id}")
async def get_product(product_id: str):
	# Logic to retrieve product by id
	product = retrieve_product_by_id(product_id)
	if product:
		product["_id"] = str(product["_id"])
		product["store_id"] = str(product["store_id"])
		return product
	else:
		raise fastapi.HTTPException(status_code=404, detail="Product not found")

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

