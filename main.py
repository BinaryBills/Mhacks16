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
from langchain.chains import LLMChain
import traceback
from langchain.prompts import ChatPromptTemplate

app = FastAPI()

class SearchRequest(BaseModel):
    description: str

async def refine_prompt(llm, input):
    return "Sorry, no keywords match!"
    #keywords = "ATV Riding, Aquarium, Backcountry, Backpacking, Beaches, Biking, Boardwalk, Boating,Brewery,Camping,Canoeing,Caves,Cliffs,Colorful Rocks,Conservatory, Detroit, Disc Golf, Dunes, Fall Colors,Fishing,Forest,Fort,Fountain,Gardens,Ghost Town,Golf Course,Grand Hotel,Hiking,Hiking Trails,Historic Site,Historic Sites,Kayaking,Lake, Lake Michigan,Lake Superior,Lakefront,Lakes,Lighthouse,Logging Museum,Military Fort,Musical Fountain,Nature Trails,Picnic,Pier,Remote,River,Riverfront,Rock Formations,Sand Dunes, Scenic Overlooks,Skiing,Sunsets,Trails,Waterfalls,Wilderness,Wildlife,Wildlife Sanctuary,Winter Sports"
    #user_prompt = "You are an AI assistant whose goal is rewrite the user's text into one concise sentence and logically replace the words in the text with one or two of the following keywords: " + keywords + " User Input:" +  input
    #result = llm(user_prompt)
    #return result


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
  keywords = "ATV Riding, Aquarium, Backcountry, Backpacking, Beaches, Biking, Boardwalk, Boating,Brewery,Camping,Canoeing,Caves,Cliffs,Colorful Rocks,Conservatory, Detroit, Disc Golf, Dunes, Fall Colors,Fishing,Forest,Fort,Fountain,Gardens,Ghost Town,Golf Course,Grand Hotel,Hiking,Hiking Trails,Historic Site,Historic Sites,Kayaking,Lake, Lake Michigan,Lake Superior,Lakefront,Lakes,Lighthouse,Logging Museum,Military Fort,Musical Fountain,Nature Trails,Picnic,Pier,Remote,River,Riverfront,Rock Formations,Sand Dunes, Scenic Overlooks,Skiing,Sunsets,Trails,Waterfalls,Wilderness,Wildlife,Wildlife Sanctuary,Winter Sports"
  priming_text = "You are an AI assistant that understands and interprets descriptions of parks. Your job is to match these descriptions with a list of parks in a database. The database has a table named 'parks' with columns 'latitude', 'longitude', 'Elevation, and 'Keywords'. The 'Keywords' column contains descriptive keywords about each restaurant. Use the keywords from a description to find and recommend parks from the database that best match the description. " + " Return as many entire as you can. " + " The possible keywords are " + keywords
  
  try:
        # Create the database connection from the URI
        db = SQLDatabase.from_uri("sqlite:///parksDatabase.db")

        # Create the SQLDatabaseChain with the LLM and the database
        db_chain = SQLDatabaseChain.from_llm(llm,db, top_k=1000, return_sql = True, verbose = True)

        # Run the chain to answer a question
        answer = db_chain.run(priming_text + " Goal:" + description)
        result = await execute_cleaned_query("parksDatabase.db",answer)

        if not result:
            fixed_result = await refine_prompt(llm,description)
            result = fixed_result
            #answer =  db_chain.run(priming_text + " Goal:" + fixed_result)
            #result = await execute_cleaned_query("parksDatabase.db",answer)

    


        print(result)
        return {"result": result}
  except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    # This will print the full traceback to the console
    traceback_str = ''.join(traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__))
    print(traceback_str)

    # You can also decide to send the traceback as part of the response
    # but be careful with this in a production environment to avoid leaking sensitive information
    return JSONResponse(
        status_code=500,
        content={
            "message": "An error occurred on the server.",
            "detail": str(exc),
            # Uncomment the line below for debugging purposes only
            # "traceback": traceback_str
        },
    )


if __name__ == "__main__":
    import uvicorn
    app.add_event_handler("startup", set_api_key)
    uvicorn.run(app, host="0.0.0.0", port=8003)

    




