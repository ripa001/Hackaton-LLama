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
                    },
                    "lat": {
                        "type": "number",
                        "description": "The latitude of the user's location.",
                    },
                    "long": {
                        "type": "number",
                        "description": "The longitude of the user's location.",
                    },
                },
                "required": [
                    "product_name_in_italian",
                ],
                "additionalProperties": False
            }
        }
    }
]


# @th.register_local_tool("get_minor_price_shop")
# def get_minor_price_shop(
#    # Must match the name of the parameters in your tool definition
#     product_name: str) -> str:
#     data = list(mongo["products"].aggregate([
#         {
#             "$match": {
#                 "full_name": {"$regex": f".*{product_name}.*"}
#             }
#         },
#         {
#             "$sort": {
#                 "price": 1
#             }
#         },
#         {
#             "$limit": 3
#         },
#         {
#             "$lookup": {
#                 "from": "stores",
#                 "localField": "store_id",
#                 "foreignField": "_id",
#                 "as": "store"
#             }
#         },
#         {"$project": {
#             "address": "$store.street", 
#             "city": "$store.city",
#             "zip_code": "$store.zip_code",
#             "working_hours": "$store.working_hours",
#             "price": 1,
#         }}
#     ]))

#     return str(data)


@th.register_local_tool("get_minor_price_shop")
def get_minor_price_shop(product_name: str) -> str:

    vector = get_text_embedding(product_name)

    wanted_fields = ["_id", "full_name", "price", "store_id", "lat", "long"]

    docs = mongo.vector_search(vector, mongo.mongo["selected_products"], limit=10, projects={k: 1 for k in wanted_fields})

    docs.sort(key=lambda x: x["price"])

    for d in docs:
        d["_id"] = str(d["_id"])
        d["store_id"] = str(d["store_id"])
        d["distance"] = ((d["lat"] - 0) ** 2 + (d["long"] - 0) ** 2) ** 0.5

    return docs[:3]


