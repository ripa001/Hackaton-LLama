import requests, json
from typing import List

from lib.config import INDEXER_URL, INDEXER_HEADER
from lib import mongo


def get_text_embedding(txt: str) -> List[float]:
	response = requests.get(INDEXER_URL + "/text-embedder", data=json.dumps({"text": txt}), headers=INDEXER_HEADER)
	if response.status_code != 200:
		print(f"failed to fetch vector, title was: {txt}, response: {response.status_code}, {response.text}")
		return None
	try:
		return json.loads(response.text)["vector"]
	except Exception as err:
		print(f"failed to parse response from indexer (text), got: {response.text}, error: {err}")
		return None


if __name__ == "__main__":

    vector = get_text_embedding("apple")

    docs = mongo.vector_search(vector, mongo.mongo["selected_products"], limit=3)

    print(docs)

	