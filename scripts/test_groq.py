import os

from toolhouse import Toolhouse
# 👋 Make sure you've also installed the Groq SDK through: pip install groq
from groq import Groq
from lib import mongo
from scripts.insert_vectors import get_text_embedding

th = Toolhouse()
client = Groq(api_key=os.getenv("API_KEY_GROQ"))

MODEL = "llama-3.1-70b-versatile"

my_local_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_minor_price_shop",
            "description": "Retrieves the document with the lowest price of a product. When you specify the product_name, IT IS CRUCIAL THAT YOU DO NOT SPECIFY ANYTHING ELSE. Before you use this tool, ensure that you only send the product_name of the product you know. If you are sending any other information, think again and remove any information that is not product_name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name_in_italian": {
                        "type": "string",
                        "description": "The name of the product the user is looking for, BUT MUST BE TRANSLATED IN ITALIAN.",
                    }
                },
                "required": [
                    "product_name_in_italian",
                ],
                "additionalProperties": False
            }
        }
    }
]


@th.register_local_tool("get_minor_price_shop")
def get_minor_price_shop(
   # Must match the name of the parameters in your tool definition
    product_name_in_italian: str, lat: float, long: float) -> str:
    print("eureka, received the tool call, lat, long", lat, long)

    data = list(mongo.mongo["products"].aggregate([
        {
            "$match": {
                "full_name": {"$regex": f".*{product_name_in_italian}.*"}
            }
        },
        {
            "$sort": {
                "price": 1
            }
        },
        {
            "$limit": 3
        },
        {
            "$lookup": {
                "from": "stores",
                "localField": "store_id",
                "foreignField": "_id",
                "as": "store"
            }
        },
        {"$project": {
            "address": "$store.street", 
            "city": "$store.city",
            "zip_code": "$store.zip_code",
            "working_hours": "$store.working_hours",
            "price": 1,
        }}
    ]))

    return str(data)


def receive_message(message: str, lat: float, long: float):

    print(message, lat, long)

    messages = [
        {"role": "system", "content": """\
You are an helpfull assistant helping users to find cheap products from local stores.\
The customers want those products as cheap as possible, but still caring about the distance to the store.\
So, you should help them to find the store that has the cheapest product and is near to them, possibibly balancing the two depending on the your judgement. \
Any other question from the users are to be ignored, and invite the user to don't go off topic.\
Do not care about the user location, we will provide this information to the various tools you can use. \
"""},
        {"role": "user", "content": message}
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        # Passes Code Execution as
        # a tool
        tools=th.get_tools() + my_local_tools,
    )

    print("response\n", response, "\n\n")
    # response = ChatCompletion(id='chatcmpl-ca3b1c05-cbd1-452f-86a2-b774dc3b2ea8', choices=[Choice(finish_reason='tool_calls', index=0, logprobs=None, message=ChatCompletionMessage(content=None, role='assistant', function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_xqg4', function=Function(arguments='{"product_name_in_italian": "vino", "lat": 45.4642, "long": 9.1895}', name='get_minor_price_shop'), type='function')]))], created=1733009893, model='llama-3.1-70b-versatile', object='chat.completion', system_fingerprint='fp_9260b4bb2e', usage=CompletionUsage(completion_tokens=39, prompt_tokens=1013, total_tokens=1052, completion_time=0.156, prompt_time=0.183215251, queue_time=0.003688129000000012, total_time=0.339215251), x_groq={'id': 'req_01jdzq0sywewbv9czb9p61dee6'}

    # Runs the Code Execution tool, gets the result,
    # and appends it to the context
    # check if in the response, the "get_minor_price_shop" tool was used
    import json

    if response.choices[0].finish_reason == "tool_calls":

        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "get_minor_price_shop":

                tool_call.function.arguments = json.loads(tool_call.function.arguments)
                ## TODO: ovverride the lat and long in the tool call
                tool_call.function.arguments["lat"] = lat
                tool_call.function.arguments["long"] = long
                tool_call.function.arguments = json.dumps(tool_call.function.arguments)
                print("tool_call", tool_call)

    tool_run = th.run_tools(response)
    print("\ntool_run\n", tool_run, "\n")

    messages.extend(tool_run)

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        # tools=th.get_tools(),
    )
    return {"message": response.choices[0].message.content}


if __name__ == "__main__":

    message = "I am looking for a cheap wine in shop near me."

    response = receive_message(message, 41.7681013, 12.3224347)
    
