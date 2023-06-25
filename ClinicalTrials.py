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
import asyncio

DEBUG=True
modelsAvailable=['GPT', 'LANGCHAIN']


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
        openai_api_version=os.getenv('OPENAI_API_VERSION'),#"2023-03-15-preview",
        deployment_name=os.getenv('OPENAI_API_CHAT_COMPLETION'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        openai_api_type = "azure",
    )
    return model


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
async def generate_query_output(user_input="", model_to_use=""):
    #append user input to history and messages
    if user_input != "":
        #st.write(model_to_use)
        if str(model_to_use)=='LANGCHAIN':
            if st.session_state['agent'] is not None:
                #Below is not awaitable
                output= st.session_state['agent'].run(st.session_state['messages']) 
        elif str(model_to_use)=='GPT':
            #Azure version of the code
            openai.api_type = "azure"
            openai.api_base = os.getenv('OPENAI_API_BASE')
            openai.api_version = os.getenv('OPENAI_API_VERSION')#"2023-03-15-preview"
            openai.api_key = os.getenv("OPENAI_API_KEY")
            completion= await openai.ChatCompletion.acreate(
               engine=os.getenv('OPENAI_API_CHAT_COMPLETION'),
                messages = st.session_state['messages'],
                temperature=0.7,
                #max_tokens=800,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None)
            
            return completion.choices[0].message.content
        else:
            st.write("No model found")
            output="Sorry I dont know the answer"
        return output          
  
    

#@st.cache_data breaks the way the controls function
def getNewData():
    st.session_state['refreshData'] = True
    st.session_state['condition']=st.session_state.condition_value
    st.session_state['treatment']=st.session_state.treatment_value
    st.session_state['location']=st.session_state.location_value
    st.session_state['other']=st.session_state.other_value
    st.session_state['studystatus']=st.session_state.studystatus_value
    st.session_state['model']=modelsAvailable.index(st.session_state.model_value)

def initializeSessionVariables():
    if 'homePageVisited' not in st.session_state:
        if 'studyDetailPageVisited' in st.session_state:
            if 'trials' in st.session_state and st.session_state['trials'] is not None: 
                if 'refreshData' in st.session_state:
                    st.session_state['refreshData']=True
                if 'refreshChat' in st.session_state:
                    st.session_state['refreshChat']=True
                if 'messages' in st.session_state:
                    st.session_state['messages']=[]

            #delete studyDetailPageVisited
            del st.session_state['studyDetailPageVisited']
        #create the fact they visited
        st.session_state['homePageVisited']=True

    if 'refreshData' not in st.session_state:
        st.session_state['refreshData'] = False
    if 'refreshChat' not in st.session_state:
        st.session_state['refreshChat'] = False
    if 'trials' not in st.session_state:
        st.session_state['trials']=None
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
    if 'condition' not in st.session_state:
        st.session_state['condition']=""
    if 'treatment' not in st.session_state:
        st.session_state['treatment']=""
    if 'location' not in st.session_state:
        st.session_state['location']=""
    if 'other' not in st.session_state:
        st.session_state['other']=""
    if 'studystatus' not in st.session_state:
        st.session_state['studystatus']=[]
    if 'model' not in st.session_state:
        st.session_state['model']=0




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
 

#endregion

async def main():

    st.set_page_config(page_title="Clinical Trials Companion",  page_icon=":robot_face:", layout="wide")
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 




    #region Begin Main UI Code
    initializeSessionVariables()


    #region ---- SIDEBAR ----
    st.sidebar.header("Specify what trials you are looking for:")
    condition=st.sidebar.text_input("Condition or Disease", value=f"{st.session_state['condition']}", placeholder="Example: Obesity",on_change=getNewData, key="condition_value")
    treatment=st.sidebar.text_input("Treament/Intervention", value=f"{st.session_state['treatment']}", placeholder="Example: Ozempic", on_change=getNewData, key="treatment_value")
    location=st.sidebar.text_input("Location City", value=f"{st.session_state['location']}", placeholder="Example: Houston", on_change=getNewData, key="location_value")
    other=st.sidebar.text_input("Other terms", value=f"{st.session_state['other']}", placeholder="Example: Pfizer", on_change=getNewData, key="other_value")


    studyStatus=st.sidebar.multiselect("Status", ['ACTIVE_NOT_RECRUITING', 'COMPLETED', 'ENROLLING_BY_INVITATION', 'NOT_YET_RECRUITING',
                                                'RECRUITING', 'SUSPENDED', 'TERMINATED', 'WITHDRAWN'
                                                'AVAILABLE','NO_LONGER_AVAILABLE', 'TEMPORARILY_NOT_AVAILABLE',
                                                'APPROVED_FOR_MARKETING','WITHHELD','UNKNOWN'],
                                                default=st.session_state['studystatus'],
                                                on_change=getNewData, key="studystatus_value")
    modelToUse=st.sidebar.selectbox("Model", modelsAvailable, on_change=getNewData, index=st.session_state['model'], key="model_value")

    search=st.sidebar.button("Find and Chat")

    #endregion------END of SIDEBAR ----

    #region-----MAIN WINDOW--------

    st.title(":robot_face: Clinical Trials Demo GPT Companion")





    #region expander
    expander=st.expander("", expanded=True)
    with expander:
        if condition or treatment or location or studyStatus or other:
            st.subheader("Welcome! Enter your choices and chat")
            st.write(f"""You currenct search criteria is: Condition is :blue[{condition if condition else 'None'}], Treatment is :blue[{treatment if treatment else 'None'}], 
                    Location is :blue[{location if location else 'None'}] 
                    Study status is :blue[{studyStatus}] Other terms are :blue[{other}], 
                    Model selected is :blue[{modelToUse}]""")
            
            st.info("""Given this is a demo we summarize the inclusion/exclusion criteria, bring back limited fields and restrict 
                        location city/facility  to 5 and results to limited number of records. You can remove these limitations
                        in your production application
                    """, icon="ℹ️")
        else:
            st.subheader("Welcome!")
            st.markdown("Enter your choices  and chat")
    #endregion

    #left_column,  right_column = st.columns([.5,.5])

    #if condition or treatment or location:
    #if search or condition or treatment or location:
    if search or st.session_state['refreshData']:
        trials=CT.Trials(CT.TrialsQuery(condition, treatment, location, studyStatus, other))
        await asyncio.create_task(trials.getStudies())

        #st.write("Getting fresh data")
        #write info in session state
        st.session_state['trials']=trials
        st.session_state['df']=trials.getStudiesAsDF()
        try:
            st.session_state['json']=trials.getStudiesAsJson()
        except:
            #f
            pass
        
        st.session_state['refreshData']=False
        st.session_state['noOfStudies']=trials.totalCount
        st.session_state['recordsShown']=len(trials.studies)
        st.session_state['generated'] = []
        st.session_state['past'] = []
        st.session_state['messages']=[]

        
        if  modelToUse=='LANGCHAIN':
            #st.write("Here to generate prompt for langchain")
            st.session_state['agent']=create_pandas_dataframe_agent(getChatModel(),st.session_state['df']) 
            st.session_state['messages']=generate_system_prompt_langchain()
        else:
        
            st.session_state['messages']=generate_system_prompt_gpt(st.session_state['json'])

            #st.write(f"Message in session state Now={st.session_state['messages']}")

    #with left_column:
        with expander:
            l, r = st.columns([.3,.8])
            with l:
                st.metric("No of Studies", st.session_state['noOfStudies'])
            with r:
                st.metric("Records shown", st.session_state['recordsShown']) 
    
        
    if not st.session_state['trials'] is None:
        st.session_state['df']=st.session_state['trials'].getStudiesAsDF()
        try: 
            st.session_state['json']=st.session_state['trials'].getStudiesAsJson()
            #st.write(st.session_state['json'])
        except:
            #st.write("Error in json")
            pass
        #with left_column:    
        with expander:

            st.dataframe(data=st.session_state['df'], use_container_width=True, hide_index=True)
            
            #st.divider()
            #st.write(st.session_state['df'].to_json(orient="records", lines=True))
            #st.write(st.session_state['df'].to_csv(sep='\t'))
        #with right_column:
    
        #end of UI and start of chat block
        st.info("Now that you have data, you can ask questions of it and GPT Companion will answer them for you", icon="ℹ️")
            
        # container for chat history
        response_container = st.container()
        # container for text box
        container = st.container()

        with container:
            with st.form(key='my_form', clear_on_submit=True):
                user_input = st.text_area("You:", key='input_home', height=100)
                submit_button = st.form_submit_button(label='Send')
                clear_button = st.form_submit_button(label="Clear Conversation")


            if (submit_button or st.session_state['refreshChat']) and user_input:
                with response_container:

                    #Append the user input
                    st.session_state['past'].append(user_input)
                    st.session_state['messages'].append({"role": "user", "content": user_input})
                    
                    with st.spinner('GPT Getting answers for you...'):
                        try: 
                            
                            output=await asyncio.create_task(generate_query_output(user_input, str(modelToUse)))

                            #Another way to do this is
                            #way1
                            #loop = asyncio.new_event_loop()
                            #asyncio.set_event_loop(loop)
                            #coro=generate_query_output(user_input, modelToUse)
                            #output=loop.run_until_complete(coro)
                            #way2
                            #tsk=loop.create_task(generate_query_output(user_input, modelToUse))
                            #loop.run_until_complete(asyncio.wait([tsk]))
                            #output=tsk.result()
                            #original synchronus way
                            #output=generate_query_output(user_input, modelToUse)
                        except Exception as e:
                            #pass
                            #st.write(e)
                            output="Sorry I dont know the answer to that"

                        #Append the out from model
                        st.session_state['generated'].append(output)
                    
                        st.session_state['messages'].append({"role": "assistant", "content": output})       
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




if __name__=="__main__":
        asyncio.run(main())
