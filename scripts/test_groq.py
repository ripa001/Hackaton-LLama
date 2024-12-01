import os

from toolhouse import Toolhouse
# 👋 Make sure you've also installed the Groq SDK through: pip install groq
from groq import Groq
from lib import mongo
import json

th = Toolhouse()
client = Groq(api_key=os.getenv("API_KEY_GROQ"))

MODEL = "llama-3.1-70b-versatile"
# MODEL = "llama-3.1-8b-instant"

my_local_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_minor_price_shop",
            "description": "Retrieves the document with the lowest price of a product, from already near-by shops. DO NOT WORRY ABOUT THE LOCALISATION, WE'LL CHECK THIS ON OUR END WITHIN THE TOOL! When you specify the product_name, IT IS CRUCIAL THAT YOU DO NOT SPECIFY ANYTHING ELSE. Before you use this tool, ensure that you only send the product_name of the product you know. If you are sending any other information, think again and remove any information that is not product_name.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_nearest_supermarket",
            "description": "Retrieves the document with the nearest supermarket. When you specify the latitude and longitude, IT IS CRUCIAL THAT YOU DO NOT SPECIFY ANYTHING ELSE. Before you use this tool, ensure that you only send the latitude and longitude of the user position. If you are sending any other information, think again and remove any information that is not latitude and longitude.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "The latitude of the user.",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "The longitude of the user.",
                    },
                },
                "required": [
                    "latitude",
                    "longitude",
                ],
                "additionalProperties": False
            },
        }
    }
]

@th.register_local_tool("get_minor_price_shop")
def get_minor_price_shop(
   # Must match the name of the parameters in your tool definition
    product_name_in_italian: str, lat: float, long: float) -> str:
    print("eureka, received the tool call, lat, long", lat, long)

    # find top 10 shops close to the user
    shop_ids = list(mongo.mongo["stores"].aggregate([
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [float(long), float(lat)]
                },
                "distanceField": "distance",
                "maxDistance": 10000000,
                "spherical": True
            }
        },
        {
            "$limit": 10
        },
        {
            "$project": {"_id": 1, "distance": 1, "working_hours": 1, "city": 1, "zip_code": 1, "street": 1}
        }
    ]))

    shop_infos = {s["_id"]: s for s in shop_ids}
    shop_ids = list(shop_infos.keys())

    print("shop_infos", len(shop_infos), shop_infos[shop_ids[0]])
    print("shop_ids", shop_ids)
    print("product_name_in_italian", f'"{product_name_in_italian}"')

    aggregate = [
        {
            "$match": {
                "store_id": {"$in": shop_ids},
            }
        },
        {
            "$match": {
                "full_name": {"$regex": product_name_in_italian.lower().strip(), "$options": "imxs"}
            }
        },
        {
            "$sort": {"price": 1}
        },
        {
            "$limit": 5
        },
        {
            "$project": {"_id": 1, "store_id": 1, "price": 1, "full_name": 1, "description": 1}
        }
    ]
    print("aggregate", aggregate)

    prods = list(mongo.mongo["products"].aggregate(aggregate))

    # if not len(prods):
    #     prods = get_minor_price_shop_vector(product_name_in_italian)

    for p in prods:
        p["distance"] = shop_infos[p["store_id"]]["distance"]    
        p["zip_code"] = shop_infos[p["store_id"]]["zip_code"]
        p["city"] = shop_infos[p["store_id"]]["city"]
        p["street"] = shop_infos[p["store_id"]]["street"]
        p["working_hours"] = shop_infos[p["store_id"]]["working_hours"]

        p["_id"] = str(p["_id"])
        p["store_id"] = str(p["store_id"])

    return str(prods)


def receive_message(message, latitude, longitude):

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
        tools=my_local_tools,
    )

    if response.choices[0].finish_reason == "tool_calls":

        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "get_minor_price_shop":

                tool_call.function.arguments = json.loads(tool_call.function.arguments)
                ## TODO: ovverride the lat and long in the tool call
                tool_call.function.arguments["lat"] = latitude
                tool_call.function.arguments["long"] = longitude
                tool_call.function.arguments = json.dumps(tool_call.function.arguments)
                print("tool_call", tool_call)

    tool_run = th.run_tools(response)
    # mess_to_llm = messages + tool_run

    messages.extend(tool_run)

    # if len(tool_run) > 0:
    #     # TODO check role
    #     messages.append({"role": "user", "content": tool_run[-1]["content"]})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        # tools=th.get_tools(),
    )

    messages.append( {"role": "assistant", "content": response.choices[0].message.content})
    print(messages)

    return {"message": messages[-1]["content"]}


if __name__ == "__main__":

    message = "I am looking for a cheap Vermentino in a shop near me."

    response = receive_message(message, 41.7681013, 12.3224347)
    
