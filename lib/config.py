from dotenv import load_dotenv
import os

load_dotenv()

API_KEY_GROQ = os.getenv("API_KEY_GROQ")
TOOLHOUSE_API_KEY = os.getenv("TOOLHOUSE_API_KEY")
MONGODB_URL = os.getenv("MONGODB_URL")

INDEXER_URL = os.getenv('INDEXER_URL')
INDEXER_HEADER = {"x-api-key": os.getenv('INDEXER_API_KEY')}
