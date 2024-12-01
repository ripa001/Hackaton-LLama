import os

from toolhouse import Toolhouse
# 👋 Make sure you've also installed the Groq SDK through: pip install groq
from groq import Groq
from lib.mongo import mongo


th = Toolhouse()
client = Groq(api_key=os.getenv("API_KEY_GROQ"))
MODEL = "llama-3.1-8b-instant"
# MODEL = "llama-3.1-70b-versatile"

my_local_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_minor_price_shop",
                "description": "Retrieves the document with the minor price of a product. When you specify the product_name, latitude and longitude, IT IS CRUCIAL THAT YOU DO NOT SPECIFY ANYTHING ELSE. If the user is looking for a specific city, use latitude and longitude based on your knowledge of the city. Before you use this tool, ensure that you only send the product_name, latitude and longitude of the user position. If you are sending any other information, think again and remove any information that is not product_name, latitude and longitude.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "The name of the product the user is looking for.",
                        },
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
                        "product_name",
                        "latitude",
                        "longitude",
                    ],
                    "additionalProperties": False
                },
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
    product_name: str) -> str:
    data = list(mongo["products"].aggregate([
        {
            "$match": {
                "full_name": {"$regex": f".*{product_name}.*"}
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



@th.register_local_tool("get_nearest_supermarket")
def get_nearest_supermarket(
    # Must match the name of the parameters in your tool definition
    latitude: float, longitude: float) -> str:
    data = list(mongo["stores"].aggregate([
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "distanceField": "distance",
                "maxDistance": 10000,
                "spherical": True
            }
        },
        {
            "$limit": 1
        }
    ]))

    return str(data)


