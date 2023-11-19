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
    keywords = "ATV Riding, Aquarium, Backcountry, Backpacking, Beaches, Biking, Boardwalk, Boating,Brewery,Camping,Canoeing,Caves,Cliffs,Colorful Rocks,Conservatory, Detroit, Disc Golf, Dunes, Fall Colors,Fishing,Forest,Fort,Fountain,Gardens,Ghost Town,Golf Course,Grand Hotel,Hiking,Hiking Trails,Historic Site,Historic Sites,Kayaking,Lake, Lake Michigan,Lake Superior,Lakefront,Lakes,Lighthouse,Logging Museum,Military Fort,Musical Fountain,Nature Trails,Picnic,Pier,Remote,River,Riverfront,Rock Formations,Sand Dunes, Scenic Overlooks,Skiing,Sunsets,Trails,Waterfalls,Wilderness,Wildlife,Wildlife Sanctuary,Winter Sports"
    template2 = f"""You are AI Agent interested in Michigan Parks. Given a description of a park, it is your job to match these descriptions with a list of keywords. You will accomplish this task by reading the user's text and relating them to one or more keywords that is most similar to their request. Then, you will rewrite the user's text in a concise single sentence using the keywords that were most similar.  The possible keywords you are required to use are {keywords}
    Example User Prompt: I want to go to go somewhere where I can sail the sea!
    Example AI Rewritten Response: I intend to visit a park where I can engage in boating!
    Goal: Using the logic demonstrated, please rewrite {input} 
    """
    authorPrompt =  PromptTemplate(
    template=template2,
    input_variables=['ok']
    )

    result = LLMChain(llm=llm, prompt=authorPrompt, verbose=True)
    return result


async def execute_cleaned_query(db_path, query):
    # Initialize the cleaned query
    cleaned_query = query

    cleaned_query = query.strip('"')

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
   

@app.post("/search/", response_class=JSONResponse)
async def search_restaurants(request: SearchRequest):
  keywords = "ATV Riding, Aquarium, Backcountry, Backpacking, Beaches, Biking, Boardwalk, Boating,Brewery,Camping,Canoeing,Caves,Cliffs,Colorful Rocks,Conservatory, Detroit, Disc Golf, Dunes, Fall Colors,Fishing,Forest,Fort,Fountain,Gardens,Ghost Town,Golf Course,Grand Hotel,Hiking,Hiking Trails,Historic Site,Historic Sites,Kayaking,Lake, Lake Michigan,Lake Superior,Lakefront,Lakes,Lighthouse,Logging Museum,Military Fort,Musical Fountain,Nature Trails,Picnic,Pier,Remote,River,Riverfront,Rock Formations,Sand Dunes, Scenic Overlooks,Skiing,Sunsets,Trails,Waterfalls,Wilderness,Wildlife,Wildlife Sanctuary,Winter Sports"
  print("entered")
  os.environ["OPENAI_API_KEY"] = pykey.getKey()
  description = request.description
  llm = OpenAI(temperature=0, model_name='gpt-4-1106-preview')
  # Explain to the AI agent its purpose and how it should read the table
  template = f"""You are an SQlite3 AI Agent that queries a database that contains information about parks in Michigan. Given a description of a park, it is your job to match these descriptions with a list of parks in the database and create the appropriate SQL command. You will accomplish this task by reading the user's text and relating them to one or more keywords in the database that is most similar to their request even in scenarios where a keyword isn't specifically mentioned in the original text. The database has a table named 'parks' with columns 'Latitude', 'Longitude', 'Elevation, and 'Keywords'. The 'Keywords' column contains descriptive keywords about each restaurant. Return as many recommendations as possible. The possible keywords you may use are {keywords}
  Example User Prompt: I want to go to go somewhere where I can sail the sea!
  Example AI Rewritten Response: "SELECT * FROM parks WHERE Keywords LIKE '%Boating%'"
  Goal: Using the logic demonstrated, please rewrite {description} 
  """
  SQLprompt = PromptTemplate(
  template=template,
  input_variables=['ok'],
  )
    
  try:
        # Create the database connection from the URI
        db = SQLDatabase.from_uri("sqlite:///parksDatabase.db")

        # Create the SQLDatabaseChain with the LLM and the database
        db_chain = SQLDatabaseChain.from_llm(llm,db, prompt=SQLprompt, top_k=1000, return_sql = True, verbose = True)

        # Run the chain to answer a question
        answer = db_chain.run(description)
        result = await execute_cleaned_query("parksDatabase.db",answer)

        if not result:
            fixed_result = await refine_prompt(llm,description)
            result = fixed_result
            answer =  db_chain.run(description)
            result = await execute_cleaned_query("parksDatabase.db",answer)

        print(result)
        
        result_list = [
            {
                "name": place[0],
                "latitude": place[1],
                "longitude": place[2],
                "height": place[3],
                "tags": place[4],
                "information": place[5]
            }
            for place in result
        ]
        return result_list
  except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    traceback_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(traceback_str)
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
    uvicorn.run(app, host="0.0.0.0", port=8005)

    




