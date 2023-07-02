#Module will contain utility functions for the CT project
import streamlit as st
import logging
import os
import pandas as pd
import openai
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage
from langchain.agents import create_pandas_dataframe_agent
from geopy.geocoders import Nominatim
from pymed import PubMed
import asyncio
import requests
import logging




#set up loggin
@st.cache_resource
def init_logger():
    
    # add logging to console and log file
    logging.basicConfig(format='%(asctime)s (%(levelname)s) %(message)s', level=logging.ERROR,
                        datefmt='%d.%m.%Y %H:%M:%S')
    logger = logging.getLogger("CTApp")
    return logger

@st.cache_resource
def getChatModel():
    model = AzureChatOpenAI(
        openai_api_base=os.getenv('OPENAI_API_BASE'),
        openai_api_version=os.getenv('OPENAI_API_VERSION'),#"2023-03-15-preview",
        deployment_name=os.getenv('OPENAI_API_CHAT_COMPLETION'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        openai_api_type = "azure",
    )
    return model

# Find the geocode that I end up using in the location search
@st.cache_data
def findGeocode(city):
   
    try:
          
        # Specify the user_agent as your
        # app name it should not be none
        geolocator = Nominatim(user_agent="BharatTestApp")
        ret_val=geolocator.geocode(city)
        if ret_val is None:
            st.write("Error in finding geocode")
            logging.error(f"Error in finding geocode {city} ")
        return ret_val
      
    except Exception as e:
        logging.error(f"Other Error in findGeocode(): {e}")
        return None  

#get pubmed articles that match the study criteria
async def getPubmedArticles(studyID=""):
    pubmed = PubMed(tool="MyTool", email="test@clinicaltrialsgpt.com")
    results = pubmed.query(f"{studyID} [si]", max_results=5 )
    return results

# Just executes the query and provides the results (JSON)
@st.cache_data
def getQueryResultsFromCTGov(query=""):
    return requests.get(query)