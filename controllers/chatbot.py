import os

from toolhouse import Toolhouse
# 👋 Make sure you've also installed the Groq SDK through: pip install groq
from groq import Groq
from lib  import mongo, vectors


th = Toolhouse()
client = Groq(api_key=os.getenv("API_KEY_GROQ"))
# MODEL = "llama-3.1-8b-instant"
MODEL = "llama-3.1-70b-versatile"


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
    },
    {
        "type": "function",
        "function": {
            "name": "get_ingredients_and_recipe",
            "description": "Retrieves the ingredients and the recipe of a given dish. When you specify the dish_name, IT IS CRUCIAL THAT YOU DO NOT SPECIFY ANYTHING ELSE. Before you use this tool, ensure that you only send the dish_name of the dish you know. If you are sending any other information, think again and remove any information that is not dish_name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_name": {
                        "type": "string",
                        "description": "The name of the dish the user is looking for.",
                    }
                },
                "required": [
                    "dish_name",
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


# def get_minor_price_shop_vector(product_name: str) -> str:

#     vector = vectors.get_text_embedding(product_name)

#     wanted_fields = ["_id", "full_name", "price", "store_id", "lat", "long"]

#     docs = mongo.vector_search(vector, mongo.mongo["prods"], limit=10, projects={k: 1 for k in wanted_fields})

#     docs.sort(key=lambda x: x["price"])

#     for d in docs:
#         d["_id"] = str(d["_id"])
#         d["store_id"] = str(d["store_id"])
#         d["distance"] = ((d["lat"] - 0) ** 2 + (d["long"] - 0) ** 2) ** 0.5

#     return docs[:3]


@th.register_local_tool("get_nearest_supermarket")
def get_nearest_supermarket(
    # Must match the name of the parameters in your tool definition
    latitude: float, longitude: float) -> str:
    data = list(mongo.mongo["stores"].aggregate([
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

