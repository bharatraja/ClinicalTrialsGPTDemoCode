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
import json

#switch page function
def switch_page(page_name: str, query_string: str = ""):
    from streamlit.runtime.scriptrunner import RerunData, RerunException
    from streamlit.source_util import get_pages

    def standardize_name(name: str) -> str:
        return name.lower().replace("_", " ")

    page_name = standardize_name(page_name)

    pages = get_pages("streamlit_app.py")  # OR whatever your main page is called

    for page_hash, config in pages.items():
        if standardize_name(config["page_name"]) == page_name:
            raise RerunException(
                RerunData(
                    query_string=query_string,
                    page_script_hash=page_hash,
                    page_name=page_name ,
                )
            )

    page_names = [standardize_name(config["page_name"]) for config in pages.values()]

    raise ValueError(f"Could not find page {page_name}. Must be one of {page_names}")


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

# Alternalte version of that can be used to get results of multuple queries
#@st.cache_data
# async def getQueryResultsFromCTGov(query=""):
#     tsk=[asyncio.to_thread(requests.get,query)]
#     rslt=await asyncio.gather(*tsk)
#     return rslt[0]
#     

@st.cache_data
def getQueryResultsFromCTGov(query=""):
    return requests.get(query)

@st.cache_data
def getAllPatients():
    try:
        return requests.get("http://127.0.0.1:8080/patients")
    except Exception as e:
        logAppInfo("(getAllPatients):",f"Error in getting all patients ","ERROR" , e)
        return None
    
@st.cache_data
def getPatientDetails(patientID=""):
    try:
        return requests.get(f"http://127.0.0.1:8080/patients/{patientID}")
    except Exception as e:
        logAppInfo("(getPatientDetail):",f"Error in getting patient {patientID} ","ERROR" , e)
        return None
    
@st.cache_data
def generate_system_prompt_for_match(trial_eligibility="", patient_info=""):
    
    #j1=json.loads(patient_info)
    content='"You are an AI assistant that evaluates if a patient is eligibile for a given clinincal trial enrollment. Provided below is both the inclusion criteria and exclusion criteria for the trial and patient information. Using this information you recommend if the patient is a potential match for the study. If a patient meets some of the critieria you can say a potential match and recommend additional areas of investigation. Clinical Trial Eligibility Criteria: '
    content += "\n\n" +  trial_eligibility + "\n\nPatient Information: \n\n" + json.dumps(patient_info) + '"}'

    return{"role":"system","content": f"{content}"}


# Gets response from GPT
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
async def getResponseFromGPT(input=[""]):
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

