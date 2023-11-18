from langchain.llms import OpenAI
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import PromptTemplate
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import os
import time
import pykey
import json


app = FastAPI()


class SearchRequest(BaseModel):
    description: str

async def execute_cleaned_query(db_path, query):
    # Initialize the cleaned query
    cleaned_query = query

    # Remove "SQLQuery:" and any preceding text, as many times as it occurs
    while "SQLQuery:" in cleaned_query:
        # Find the index of "SQLQuery:" and extract the substring from there
        index = cleaned_query.find("SQLQuery:")
        cleaned_query = cleaned_query[index + len("SQLQuery:"):].strip()

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute the cleaned query
    cursor.execute(cleaned_query)
    
    # Fetch all results
    results = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return results


def set_api_key():
 os.environ["OPENAI_API_KEY"] = pykey.getKey()
 pass
   

@app.post("/search/")
async def search_restaurants(request: SearchRequest):
  os.environ["OPENAI_API_KEY"] = pykey.getKey()
  description = request.description
  llm = OpenAI(temperature=0, model_name='gpt-4-1106-preview')
  # Explain to the AI agent its purpose and how it should read the table
  priming_text = """
  You are an AI assistant that understands and interprets descriptions of restaurants. Your job is to match these descriptions with a list of restaurants in a database. The database has a table named 'Restaurants' with columns 'restaurant_id', 'place_name', and 'tags'. The 'tags' column contains descriptive keywords about each restaurant. Use the keywords from a description to find and recommend restaurants from the database that best match the description.
  Return as many entries as you can.
  """
  
  try:
        # Create the database connection from the URI
        db = SQLDatabase.from_uri("sqlite:///restaurants.db")

        # Create the SQLDatabaseChain with the LLM and the database
        db_chain = SQLDatabaseChain.from_llm(llm,db, top_k=1000, return_sql = True, verbose = True)

        # Run the chain to answer a question
        answer = db_chain.run(priming_text + " Goal:" + description)
        result = await execute_cleaned_query("restaurants.db",answer)
        print(result)
        return {"result": result}
  except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "An error occurred on the server.", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    app.add_event_handler("startup", set_api_key)
    uvicorn.run(app, host="0.0.0.0", port=8000)

    




