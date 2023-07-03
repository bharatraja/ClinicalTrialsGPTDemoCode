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
from tenacity import retry, wait_random_exponential, stop_after_attempt 




#set up loggin
@st.cache_resource
def init_logger():
    
    # add logging to console and log file
    logging.basicConfig(format='%(asctime)s (%(levelname)s) %(message)s', level=logging.ERROR,
                        datefmt='%d.%m.%Y %H:%M:%S')
    logger = logging.getLogger("CTApp")
    return logger

def logAppInfo(fname="",msg="", lglvl="ERROR",  excpt=None):
    if lglvl=="INFO":
        logging.info(f"{fname}: {msg}")
    if lglvl=="ERROR":
        if excpt is None:
            logging.error(f"{fname}: {msg}")
        else:
            logging.error(f"{fname}: {msg} {excpt}")
    return

#Gets the chat model for use with the langchain library
@st.cache_resource
def getChatModel():
    try:
        model = AzureChatOpenAI(
            openai_api_base=os.getenv('OPENAI_API_BASE'),
            openai_api_version=os.getenv('OPENAI_API_VERSION'),#"2023-03-15-preview",
            deployment_name=os.getenv('OPENAI_API_CHAT_COMPLETION'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_api_type = "azure",
        )
        return model
    except Exception as e:
        logAppInfo("(getChatModel):",f"Error in getting chat model ","ERROR" , e)
        return None

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
            logAppInfo("( findGeocode):",f"Error in finding geocode for {city} ")
        return ret_val
      
    except Exception as e:
        logAppInfo("( findGeocode):",f"Error in finding geocode for {city} ","ERROR" , e)
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

# Gets response from GPT
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
async def getResponseFromGPT(input=""):
    try:
        openai.api_type = "azure"
        openai.api_base = os.getenv('OPENAI_API_BASE')
        openai.api_version = os.getenv('OPENAI_API_VERSION')#"2023-03-15-preview"
        openai.api_key = os.getenv("OPENAI_API_KEY")
        completion= await openai.ChatCompletion.acreate(
                engine=os.getenv('OPENAI_API_CHAT_COMPLETION'),
                    messages = input,
                    temperature=0.7,
                    #max_tokens=800,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None)
                
        return completion.choices[0].message.content
    except Exception as e:
        logAppInfo("(getResponseFromGPT):",f"Error in getting response from GPT ","ERROR" , e)
        return None

def hideStreamlitStyle():
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

