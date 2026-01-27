from dotenv import load_dotenv
import os

load_dotenv()

print("Host:", os.getenv("PG_HOST"))  # should print 'localhost'