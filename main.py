from typing import Union
from controllers.chatbot import th, my_local_tools, MODEL, client
from lib.mongo import retrieve_product_by_id, get_user_chat, upsert_user_chat, clear_chat
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

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

@app.post("/clear-chat")
async def endpoint_clear_chat():
    return {"success": clear_chat()}

@app.post("/message")
async def receive_message(body: bodyMessage):
    # Process the message and coordinates here
    # return {"message": message, "latitude": latitude, "longitude": longitude}
    message = body.message
    latitude = body.latitude
    longitude = body.longitude
    user = body.userId

    chat = get_user_chat(user)

    print("User chat", chat)
    if chat:
        messages = chat["chat"]
    else:
        messages = [{"role": "system", "content": """\
You are an helpfull assistant helping users to find cheap products from local stores. \
The customers want those products as cheap as possible, but still caring about the distance to the store. \
So, you should help them to find the store that has the cheapest product and is near to them, possibibly balancing the two depending on the your judgement. \
Any other question from the users are to be ignored, and invite the user to don't go off topic. \
IMPORTANT: Do not care about the user location, we will provide this information to the various tools that you'll use. \
"""}]

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        # messages=[{"role": "user", "content": message}],
        # Passes Code Execution as
        # a tool
        tools=th.get_tools() + my_local_tools,
    )

    if response.choices[0].finish_reason == "tool_calls":

        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "get_minor_price_shop":

                tool_call.function.arguments = json.loads(tool_call.function.arguments)
                ## TODO: ovverride the lat and long in the tool call
                tool_call.function.arguments["lat"] = latitude
                tool_call.function.arguments["long"] = longitude
                tool_call.function.arguments = json.dumps(tool_call.function.arguments)
                print("tool_call", tool_call	)

    tool_run = th.run_tools(response)
    print("\ntool_run", tool_run, "\n")
    messages.extend(tool_run)

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        # tools=th.get_tools(),
    )

    messages.append( {"role": "assistant", "content": response.choices[0].message.content})

    print("\nresponse", messages[-1], "\n")

    upsert_user_chat(messages, user)

    return {"message": messages[-1]["content"]}


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
