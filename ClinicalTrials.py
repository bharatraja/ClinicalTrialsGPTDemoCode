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

DEBUG=True

st.set_page_config(page_title="Clinical Trials Companion",  page_icon=":bar_chart:", layout="wide")

#region TODOS
 #ICON next to Title
 #Do some optimization so we are not querying all the time
 #remove @st.cache_data from findGeocode
#endregion

def camel_case_split(str):
    #first word will 
    words = [[str[0].upper()]]

 
    for c in str[1:]:
        if words[-1][-1].islower() and c.isupper():
            words.append(list(c))
        else:
            words[-1].append(c)
 
    words= [''.join(word) for word in words]
    return ' '.join(words)



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
    

@st.cache_data
def getQueryResultsFromCTGov(query=""):
    return requests.get(query)


@st.cache_data
def findGeocode(city):
    # try and catch is used to overcome
    # the exception thrown by geolocator
    # using geocodertimedout  
    try:
          
        # Specify the user_agent as your
        # app name it should not be none
        geolocator = Nominatim(user_agent="BharatTestApp")
        return geolocator.geocode(city)
      
    except:
        return None  

#region CTCode 

#region TrialQuery
class TrialsQuery:
    condition="" #condition
    treatment="" #treament same as intervention
    location=""  #location could be a city but will expand later
    range="100mi"    #default range
    max_records=50
    lat=""
    long=""
    studyStatus=""

    #region api endpoints
    api_base="https://beta.clinicaltrials.gov/api/v2"
    api_key="" 
    api_studies="/studies"
    api_studies_detail="/studies/"
    api_studies_metadata="/studies/metadata"
    api_stats="/stats/size"
    api_field_values="/stats/fieldValues"
    api_field_detail="/stats/fieldValues/"
    api_list_size="/stats/listSizes"
    api_list_field_size="/stats/listSizes/"
    api_version="/version"
    #endregion

    def __init__(self, conditon="", treatment="", location="", studyStatus=[]):
        self.condition=condition
        self.treatment=treatment
        self.studyStatus=",".join(studyStatus)

        self.location=location
        if location != "":
            gc=findGeocode(location)
            try:
                self.lat=str(gc.latitude)
                self.long=str(gc.longitude)
            except:
                #st.write("Error in Location")
                return
           

    def getStudiesQuery(self, fields=None)->str:

        #need to urlencode
        if fields is None:
            fields="NCTId,BriefTitle,LeadSponsorName,LocationCity,LocationFacility,InterventionName,PrimaryOutcomeMeasure,BriefSummary" #cannot have spaces

        query=( self.api_base + self.api_studies + "?" +
              f"query.cond={self.condition}&" +
              f"query.intr={self.treatment}&" +
              f"fields={fields}&" +
              "countTotal=true&" +
              f"pageSize={self.max_records}&"
          )
        if self.lat != "":
            query=query + f"postFilter.geo=distance({self.lat},{self.long},{self.range})&" + f"query.locn={self.location}&"

        if self.studyStatus != "":
            query+= f"postFilter.overallStatus={self.studyStatus}&"

        #if DEBUG:
        #    st.write(f"query is {query}") 

        #st.write(urllib.parse.quote_plus(query,'/:&?='))
        return urllib.parse.quote_plus(query,'/:&?=(),')

    def __str__(self) -> str:
        return f"{{ \
            condition: {self.condition}, \
            treatment: {self.treatment}, \
            location: {self.location}, \
        }}"
    
#endregion

#region Study
class Study:
   raw=""
   nctid=""
   leadSponsor=""
   briefTitle=""
   interventionName=""
   primaryOutcomeMeasure=""
   briefSummary=""
   locationCity=""
   locationFacility=""


   def collate(self, arr=[],key=""):
       try: 
        intr=[t[key] for t in arr]
        return ', '.join(intr)
       except:
           return ""

   
   def getValueIfExists(self, keysArr=[],raw=""):
       if len(keysArr) >1 and len(raw) !=0:
           #if raw[keysArr[0]]:
           if keysArr[0] in raw:
               popped=keysArr.pop(0)
               #st.write(popped)
               #st.write(keysArr)
               return self.getValueIfExists(keysArr,raw[popped])
           else:
               return ""
       else:
           #st.write(raw)
           if len(raw) != 0:
               return raw[keysArr[0]]
           else:
               return ""
        

   def __init__(self,raw=""):
       self.raw=raw

       #process raw
       if raw != "":
           try:
               self.nctid=raw['protocolSection']['identificationModule']['nctId']
               self.briefTitle=raw['protocolSection']['identificationModule']['briefTitle']
               self.leadSponsor=raw['protocolSection']['sponsorCollaboratorsModule']['leadSponsor']['name']
               self.briefSummary=raw['protocolSection']['descriptionModule']['briefSummary']
               #if 'armsInterventionsModule' in raw['protocolSection']:
               # if 'interventions' in raw['protocolSection']['armsInterventionsModule']:
               #    self.interventionName=self.collate(raw['protocolSection']['armsInterventionsModule']['interventions'],"name")
               
               self.interventionName=self.collate( self.getValueIfExists(['armsInterventionsModule', 'interventions'],
                                                 raw['protocolSection']), 'name')
               
               self.locationFacility=self.collate( self.getValueIfExists(['contactsLocationsModule', 'locations'], 
                                                 raw['protocolSection']), 'facility')

               self.locationCity=self.collate(self.getValueIfExists(['contactsLocationsModule','locations'], 
                                                                    raw['protocolSection']), 'city')
               self.primaryOutcomeMeasure=self.collate(self.getValueIfExists(['outcomesModule', 'primaryOutcomes'],
                                                                   raw['protocolSection']), "measure")  
               
           except:
               st.write(f"Error in study data {self.nctid}")
               #st.write(raw)


           

#endregion

#region Trials Class
class Trials:
  query:TrialsQuery
  response=None
  raw_json=None
  totalCount=0
  studies=[]

  def __init__(self,query:TrialsQuery=None):
      self.query=query
      self.studies=[]

  def getStudies(self, query:TrialsQuery=None)->None:
      if query != None:
          self.query=query
      
      try:
          url=self.query.getStudiesQuery()
          r=getQueryResultsFromCTGov(url)
          self.response=r

          self.raw_json=j=r.json()
          #st.write(j)
          self.totalCount=j['totalCount']

          #studies for now studies are just nct
          self.studies=list(map (lambda x:  Study(x), j['studies']))
          #st.write(f"Total Number of studies:{self.totalCount}")
          #st.write(f"No of Studies pulled={len(self.studies)}")
          return self.response
      
      except HTTPError as err:
          st.write(f"HTTP error occured in Trials.getStudies(): {err}")
      except:
          st.write("Error")
          return None
      return None #
  
  #Returns studies as a datafram
  def getStudiesAsDF(self):
    if self.totalCount!=0:
        df = pd.DataFrame([t.__dict__ for t in self.studies ])
        df.drop(['raw'],axis=1,inplace=True)

        #write meaningful column names
        df.columns=[camel_case_split(str(n)) for n in df.columns]
        
        

        return df
    else:
        return None
   
      

#endregion

#endregion


#region Begin Main UI Code
#@st.cache_data breaks the way the controls function
def getNewData():
    st.session_state['refreshData'] = True

#@st.cache_data
def getNewChatResponse():
    st.session_state['refreshChat'] = True

@st.cache_data
def generate_message_prompt():
     return [{"role":"system","content": """You are an AI Assistant that helps interpert Clincal Trials Data in a data. study id is nctid. 
              column names in this data are combined without spaces. For example briefTitle column name should be interpreted as Brief Title.
              Here is how to use the different columns to understand data:
              nctid also know as study id the unique identification code given to each clinical study upon registration at ClinicalTrials.gov. The format is NCT followed by an 8-digit number. Also known as ClinicalTrials.gov Identifier
              Each row is a seperate study with a unique Study ID OR nctid.
              Brief Title  provides a brief title of the study. A short title of the clinical study written in language intended for the lay public. The title should include, where possible, information on the participants, condition being evaluated, and intervention(s) studied.
              Lead Sponsor (like a Pharma company) for the study. The organization or person who initiates the study and who has authority and control over the study.
              Brief summary is a smummary of the what the study aims to achieve
              Intervention Name lists out all the interventions or treatment in the study like a placebo or an actual ingredient. Arm/Group and Intervention Cross Reference
              Location Facility is the Location Facility of a Hospital where the study is conducted
              Location City is the City of where the facility is
              Primary Outcome Measure is the Primary Outcomes that are measured in the study to see if the intervention tested has any effect
              Similary with other columns. If you dont know any answer say you dont know and point to https://clinicaltrials.gov for information"""}
                ]

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def generate_query_output(user_input=""):
    if user_input != "":
         if st.session_state['agent'] is not None:
             return st.session_state['agent'].run(user_input) 

#region Initialise session state variables
if 'refreshData' not in st.session_state:
    st.session_state['refreshData'] = False
if 'refreshChat' not in st.session_state:
    st.session_state['refreshChat'] = False
if 'df' not in st.session_state:
    st.session_state['df']=None
if 'noOfStudies' not in st.session_state:
    st.session_state['noOfStudies']=0
if 'recordsShown' not in st.session_state:
    st.session_state['recordsShown']=0
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] =generate_message_prompt()
if 'agent' not in st.session_state:
    st.session_state['agent']=None
#endregion


#region ---- SIDEBAR ----
st.sidebar.header("Specify what trials you are looking for:")
condition=st.sidebar.text_input("Condition or Disease",  placeholder="Example: Obesity",on_change=getNewData)
treatment=st.sidebar.text_input("Treament/Intervention", placeholder="Example: Ozempic", on_change=getNewData)
location=st.sidebar.text_input("Location City", placeholder="Example: Houston", on_change=getNewData)


studyStatus=st.sidebar.multiselect("Status", ['ACTIVE_NOT_RECRUITING', 'COMPLETED', 'ENROLLING_BY_INVITATION', 'NOT_YET_RECRUITING',
                                              'RECRUITING', 'SUSPENDED', 'TERMINATED', 'WITHDRAWN'
                                              'AVAILABLE','NO_LONGER_AVAILABLE', 'TEMPORARILY_NOT_AVAILABLE',
                                              'APPROVED_FOR_MARKETING','WITHHELD','UNKNOWN'],
                                              on_change=getNewData)
search=st.sidebar.button("Find and Chat")

#endregion------END of SIDEBAR ----

#region-----MAIN WINDOW--------

st.title(":bar_chart: Clinical Trials Demo GPT Copilot")


with st.expander("", expanded=True):
    if condition or treatment or location or studyStatus:
        st.subheader("You current Search Criteria")
        st.write(f"""Condition is :blue[{condition if condition else 'None'}], Treatment is :blue[{treatment if treatment else 'None'}], 
                Location is :blue[{location if location else 'None'}] 
                Study status is :blue[{studyStatus}]""")
    else:
        st.subheader("Welcome!")
        st.markdown("Enter your choices  and chat")


left_column,  right_column = st.columns([.5,.5])

#if condition or treatment or location:
#if search or condition or treatment or location:
if search or st.session_state['refreshData']:
    trials=Trials(TrialsQuery(condition, treatment, location, studyStatus))
    trials.getStudies()

 

    #st.write("Getting fresh data")
    #write info in session state
    st.session_state['df']=trials.getStudiesAsDF()
    st.session_state['refreshData']=False
    st.session_state['noOfStudies']=trials.totalCount
    st.session_state['recordsShown']=len(trials.studies)
    if not st.session_state['df'] is None:
        st.session_state['agent']=create_pandas_dataframe_agent(getChatModel(),st.session_state['df']) 


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
                    with st.spinner('GPT Getting answers for you...'):
                        try:
                            #output=st.session_state['agent'].run(user_input)
                            output=generate_query_output(user_input)
                        except:
                            #st.write()
                            output="Sorry I dont know the answer to that"

                st.session_state['past'].append(user_input)
                st.session_state['generated'].append(output)
                
                st.session_state['messages'].append({"role": "user", "content": user_input})
                st.session_state['messages'].append({"role": "assistant", "content": output})

                #st.write(st.session_state['messages'])

           
                st.session_state['refreshChat']=False

            # reset everything
            if clear_button:
                st.session_state['generated'] = []
                st.session_state['past'] = []
                st.session_state['messages'] = generate_message_prompt()


        if st.session_state['generated']:
            with response_container:
                for i in range(len(st.session_state['generated'])):
                    message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
                    message(st.session_state["generated"][i], key=str(i))


        
#end of UI for pulling data from clinicaltrials.gov



#st.write(findGeocode('oak park, illinois').latitude) 
#endregion----End Main Window
#endregion -- End UI Code
