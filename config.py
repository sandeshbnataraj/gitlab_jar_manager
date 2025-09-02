import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()
# Read the private token from an environment variable
PRIVATE_TOKEN = os.getenv("PRIVATE_TOKEN")
if not PRIVATE_TOKEN:
    raise ValueError("No private token provided from '.env'")

PROJECT_ID = 121 # personal EWSclient project

DEFAULT_GROUP_ID = "com.ilts.libs"

#current pyhon proj path
PYTHON_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

JAR_FOLDER_PATH = os.path.abspath(os.path.join(PYTHON_PROJECT_ROOT,"..","lib"))

#SAVED_JSON = os.path.abspath(os.path.join(PYTHON_PROJECT_ROOT,"..",'library.json'))
SAVED_JSON = "library.json"

DOWNLOADED_JAR_PATH = os.path.abspath(os.path.join(PYTHON_PROJECT_ROOT,"..","lib"))