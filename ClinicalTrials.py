import openai
import streamlit as st
from streamlit_chat import message
import requests
from requests.exceptions import HTTPError
import json
import urllib.parse
import os
from geopy.geocoders import Nominatim
import pandas as pd
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage
from langchain.agents import create_pandas_dataframe_agent
from tenacity import retry, wait_random_exponential, stop_after_attempt 
import ClinicalTrialClasses as CT

DEBUG=True

st.set_page_config(page_title="Clinical Trials Companion",  page_icon=":robot_face:", layout="wide")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

#region TODOS
 #ICON next to Title
 #Do some optimization so we are not querying all the time
 #remove @st.cache_data from findGeocode
#endregion

#region Functions
@st.cache_resource
def getChatModel():
    model = AzureChatOpenAI(
        openai_api_base=os.getenv('OPENAI_API_BASE'),
        openai_api_version="2023-03-15-preview",
        deployment_name=os.getenv('OPENAI_API_CHAT_COMPLETION'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        openai_api_type = "azure",
    )
    return model


    
    

#@st.cache_data breaks the way the controls function
def getNewData():
    st.session_state['refreshData'] = True

#@st.cache_data
def getNewChatResponse():
    st.session_state['refreshChat'] = True

@st.cache_data
def generate_system_prompt_langchain(model_to_use='', data=""):
    
    return [{"role":"system","content": """You are an AI Assistant that helps interpert Clincal Trials Data in a data. study id is nctid. 
              column names in this data are combined without spaces. For example briefTitle column name should be interpreted as Brief Title.
              Here is how to use the different columns to understand data:
              nctid also know as study id the unique identification code given to each clinical study upon registration at ClinicalTrials.gov. The format is NCT followed by an 8-digit number. Also known as ClinicalTrials.gov Identifier
              Each row in the dataframe provided is a seperate study with a unique Study ID OR nctid.
              Brief Title  provides a brief title of the study. A short title of the clinical study written in language intended for the lay public. The title should include, where possible, information on the participants, condition being evaluated, and intervention(s) studied.
              Lead Sponsor (like a Pharma company) for the study. The organization or person who initiates the study and who has authority and control over the study.
              Brief summary is a smummary of the what the study aims to achieve
              Intervention Name lists out all the interventions or treatment in the study like a placebo or an actual ingredient. Arm/Group and Intervention Cross Reference
              Location Facility is the Location Facility of a Hospital where the study is conducted
              Location City is the City of where the facility is
              Primary Outcome Measure is the Primary Outcomes that are measured in the study to see if the intervention tested has any effect
              Similary with other columns. If you dont know any answer say you dont know and point to https://clinicaltrials.gov for information"""}
                ]

#@st.cache_data
def generate_system_prompt_gpt(data=""):
    return [{"role":"system","content": f"""You are an AI assistant that answers questions on Clinical trials studies information provided as json below:
                {data}                
                """}]
 
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def generate_query_output(user_input="", model_to_use=""):
    #append user input to history and messages
    if user_input != "":
        #st.write(model_to_use)
        if str(model_to_use)=='LANGCHAIN':
            if st.session_state['agent'] is not None:
                #st.write(st.session_state['messages'])
                output=st.session_state['agent'].run(st.session_state['messages']) 
        elif str(model_to_use)=='GPT':
            #Azure version of the code
            st.write(st.session_state['messages'])
            completion = openai.ChatCompletion.create(
                engine=os.getenv('OPENAI_API_CHAT_COMPLETION'),
                messages = st.session_state['messages'],
                temperature=0.7,
                #max_tokens=800,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None)
            
            st.write("After getting data")
            output=completion.choices[0].message.content
            st.write("Before sending back")
        else:
            st.write("No model found")
            output="Sorry I dont know the answer"
        return output          
#endregion

#region Begin Main UI Code


#region Initialise session state variables
if 'refreshData' not in st.session_state:
    st.session_state['refreshData'] = False
if 'refreshChat' not in st.session_state:
    st.session_state['refreshChat'] = False
if 'df' not in st.session_state:
    st.session_state['df']=None
if 'json' not in st.session_state:
    st.session_state['json']=""
if 'noOfStudies' not in st.session_state:
    st.session_state['noOfStudies']=0
if 'recordsShown' not in st.session_state:
    st.session_state['recordsShown']=0
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] =[]
if 'agent' not in st.session_state:
    st.session_state['agent']=None
#endregion


#region ---- SIDEBAR ----
st.sidebar.header("Specify what trials you are looking for:")
condition=st.sidebar.text_input("Condition or Disease",  placeholder="Example: Obesity",on_change=getNewData)
treatment=st.sidebar.text_input("Treament/Intervention", placeholder="Example: Ozempic", on_change=getNewData)
location=st.sidebar.text_input("Location City", placeholder="Example: Houston", on_change=getNewData)
other=st.sidebar.text_input("Other terms", placeholder="Example: Pfizer", on_change=getNewData)


studyStatus=st.sidebar.multiselect("Status", ['ACTIVE_NOT_RECRUITING', 'COMPLETED', 'ENROLLING_BY_INVITATION', 'NOT_YET_RECRUITING',
                                              'RECRUITING', 'SUSPENDED', 'TERMINATED', 'WITHDRAWN'
                                              'AVAILABLE','NO_LONGER_AVAILABLE', 'TEMPORARILY_NOT_AVAILABLE',
                                              'APPROVED_FOR_MARKETING','WITHHELD','UNKNOWN'],
                                              on_change=getNewData)
modelToUse=st.sidebar.selectbox("Model", ['GPT', 'LANGCHAIN'], on_change=getNewData)

search=st.sidebar.button("Find and Chat")

#endregion------END of SIDEBAR ----

#region-----MAIN WINDOW--------

st.title(":robot_face: Clinical Trials Demo GPT Copilot")


#region expander
with st.expander("", expanded=True):
    if condition or treatment or location or studyStatus or other:
        st.subheader("Welcome! Enter your choices and chat")
        st.write(f"""You currenct search criteria is: Condition is :blue[{condition if condition else 'None'}], Treatment is :blue[{treatment if treatment else 'None'}], 
                Location is :blue[{location if location else 'None'}] 
                Study status is :blue[{studyStatus}] Other terms are :blue[{other}], 
                Model selected is :blue[{modelToUse}]""")
        
        st.warning("""Given this is a demo we summarize the inclusion/exclusion criteria, bring back limited fields and restrict 
                       location city/facility  to 5 and results to limited number of records. You can remove these limiations
                       in your production application
                """)
    else:
        st.subheader("Welcome!")
        st.markdown("Enter your choices  and chat")
#endregion

left_column,  right_column = st.columns([.5,.5])

#if condition or treatment or location:
#if search or condition or treatment or location:
if search or st.session_state['refreshData']:
    trials=CT.Trials(CT.TrialsQuery(condition, treatment, location, studyStatus, other))
    trials.getStudies()

    #st.write("Getting fresh data")
    #write info in session state
    st.session_state['df']=trials.getStudiesAsDF()
    st.session_state['json']=trials.getStudiesAsJson()
    st.session_state['refreshData']=False
    st.session_state['noOfStudies']=trials.totalCount
    st.session_state['recordsShown']=len(trials.studies)
    st.session_state['generated'] = []
    st.session_state['past'] = []

    
    if  modelToUse=='LANGCHAIN':
        #st.write("Here to generate prompt for langchain")
        st.session_state['agent']=create_pandas_dataframe_agent(getChatModel(),st.session_state['df']) 
        st.session_state['messages']=generate_system_prompt_langchain()
    else:
        st.session_state['messages']=generate_system_prompt_gpt(st.session_state['json'])
        #st.write(f"Message in session state Now={st.session_state['messages']}")

with left_column:
        l, r = st.columns([.3,.8])
        with l:
            st.metric("No of Studies", st.session_state['noOfStudies'])
        with r:
            st.metric("Records shown", st.session_state['recordsShown']) 
   
    
if not st.session_state['df'] is None:
    with left_column:    
        st.dataframe(data=st.session_state['df'], use_container_width=True, hide_index=True)
        st.divider()
        #st.write(st.session_state['df'].to_json(orient="records", lines=True))
        #st.write(st.session_state['df'].to_csv(sep='\t'))
    with right_column:
   
        #end of UI and start of chat block
        st.markdown(":blue[Now that you have data, you can ask questions of it and GPT Companion will answer them for you]")
        
        # container for chat history
        response_container = st.container()
        # container for text box
        container = st.container()

        with container:
            with st.form(key='my_form', clear_on_submit=True):
                user_input = st.text_area("You:", key='input', height=100)
                submit_button = st.form_submit_button(label='Send')
                clear_button = st.form_submit_button(label="Clear Conversation")


            if (submit_button or st.session_state['refreshChat']) and user_input:
                with response_container:

                    #Append the user input
                    st.session_state['past'].append(user_input)
                    st.session_state['messages'].append({"role": "user", "content": user_input})
                
                    with st.spinner('GPT Getting answers for you...'):
                        #try:
                            #output=st.session_state['agent'].run(user_input)
                            output=generate_query_output(user_input, modelToUse)
                        #except:
                            #output="Sorry I dont know the answer to that"

                #Append the out from model
                st.session_state['generated'].append(output)
                
                st.session_state['messages'].append({"role": "assistant", "content": output})                #st.write(st.session_state['messages'])
                st.session_state['refreshChat']=False

            # reset everything
            if clear_button:
                st.session_state['generated'] = []
                st.session_state['past'] = []
                st.session_state['messages'] = []
                if modelToUse=='GPT':
                    st.session_state['messages']=generate_system_prompt_gpt(st.session_state['json'])

        if st.session_state['generated']:
            with response_container:
                for i in range(len(st.session_state['generated'])):
                    message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
                    message(st.session_state["generated"][i], key=str(i))


        
#end of UI for pulling data from clinicaltrials.gov



#st.write(findGeocode('oak park, illinois').latitude) 
#endregion----End Main Window
#endregion -- End UI Code
