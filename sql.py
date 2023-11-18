from langchain.llms import OpenAI
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import PromptTemplate

import sqlite3

def execute_cleaned_query(db_path, query):
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
# Explain to the AI agent its purpose and how it should read the table
priming_text = """
You are an AI assistant that understands and interprets descriptions of restaurants. Your job is to match these descriptions with a list of restaurants in a database. The database has a table named 'Restaurants' with columns 'restaurant_id', 'place_name', and 'tags'. The 'tags' column contains descriptive keywords about each restaurant. Use the keywords from a description to find and recommend restaurants from the database that best match the description.
Return as many entries as you can.
"""
prompt_template = PromptTemplate.from_template(priming_text)
try:
    # Initialize the LLM with the desired parameters
    llm = OpenAI(temperature=0, model_name='gpt-4-1106-preview')

    # Create the database connection from the URI
    db = SQLDatabase.from_uri("sqlite:///restaurants.db")

    # Create the SQLDatabaseChain with the LLM and the database
    db_chain = SQLDatabaseChain.from_llm(llm,db, top_k=1000, return_sql = True, verbose = True)

    # Run the chain to answer a question

    
    answer = db_chain.run(priming_text + " Goal:" + "I am pretty hungry right now, and I do not have much time to wait? Where can I go that won't take long to prepare the food?")
    result = execute_cleaned_query("restaurants.db",answer)
    print(result)
except Exception as e:
    print(f"An error occurred: {e}")
