#Provides all supporting classes for ClinicalTrials.py


import streamlit as st
import openai
from langchain.chat_models import AzureChatOpenAI
import requests
from requests.exceptions import HTTPError
import json
import urllib.parse
import os
from geopy.geocoders import Nominatim
import pandas as pd
from langchain.schema import HumanMessage
import asyncio
import os

#region TODOS

#endregion

DEBUG=True

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

# async def getSummary(model=None, raw=""):
#     if model is not None:
#         try:
           
#             msg=f"Summarize the below:\n\n {raw}"
#             st.write(msg)
#             return await (model( [ HumanMessage(content=msg)]).content)
#             #st.write(output)
#              #return output
#         except:
#              return ""
   
    
async def getSummary(raw=""):
    openai.api_type = "azure"
    openai.api_base = os.getenv('OPENAI_API_BASE')
    openai.api_version = os.getenv('OPENAI_API_VERSION')#"2023-03-15-preview"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    msg=[{"role":"system","content": "You are an AI assistant that summarizes Clinical Trials Study  eligibility Criteria"},
          {"role": "user", "content": f"""Please summarize the below  
                {raw}                
                """}]

    completion= await openai.ChatCompletion.acreate(
               engine=os.getenv('OPENAI_API_CHAT_COMPLETION'),
                messages = msg,
                temperature=0.7,
                #max_tokens=800,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None)
            
    return completion.choices[0].message.content


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

#region CTCode 

#region TrialQuery
class TrialsQuery:
    condition="" #condition
    treatment="" #treament same as intervention
    location=""  #location could be a city but will expand later
    range="100mi"    #default range
    max_records=os.getenv('GPT_DEMO_MAX_RECORDS_TO_RETURN')
    lat=""
    long=""
    studyStatus=""
    other=""
    study_id="" #to get a study detail

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

    def __init__(self, condition="", treatment="", location="", studyStatus=[], other="",study_id=""):
        self.condition=condition
        self.treatment=treatment
        self.studyStatus=",".join(studyStatus)
        self.study_id=study_id

        self.location=location
        self.other=other
        if location != "":
            gc=findGeocode(location)
            try:
                self.lat=str(gc.latitude)
                self.long=str(gc.longitude)
            except:
                #st.write("Error in Location")
                return

    def getStudyDetailQuery(self,  fields=None)->str:
        if self.study_id != "":
            query= self.api_base + self.api_studies_detail + self.study_id
            return urllib.parse.quote_plus(query,'/:&?=(),')
        else:
            return ""


    def getStudiesQuery(self, fields=None)->str:

        #need to urlencode
        if fields is None:
            fields="NCTId,BriefTitle,LeadSponsorName,LocationCity,LocationFacility,InterventionName,PrimaryOutcomeMeasure,BriefSummary,OverallStatus,Phase,Sex,EligibilityCriteria" #cannot have spaces

        query=( self.api_base + self.api_studies + "?" +
              f"query.cond={self.condition}&" +
              f"query.intr={self.treatment}&" +
              f"query.term={self.other}&" +
              f"fields={fields}&" +
              "countTotal=true&" +
              f"pageSize={self.max_records}&"
          )
        if self.lat != "":
            query=query + f"postFilter.geo=distance({self.lat},{self.long},{self.range})&" + f"query.locn={self.location}&"

        if self.studyStatus != "":
            query+= f"postFilter.overallStatus={self.studyStatus}&"

        #if DEBUG:
        #    st.write(urllib.parse.quote_plus(query,'/:&?='))

        
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
   status=""
   phases=""
   eligibilityCriteria=""
   sex=""

   #limit restircs how many elements of the array we collate this is the prevent the 
   # number of tokens sent to gpt  
   def collate(self, arr=[],key="", limit=0):
       if limit!=0:
           arr=[t for i, t in enumerate(arr)
                                if i < limit]
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
      
   async def processStudy(self):

       #process raw
       if self.raw != "":
           try:
               self.nctid=self.raw['protocolSection']['identificationModule']['nctId']
               self.briefTitle=self.raw['protocolSection']['identificationModule']['briefTitle']
               self.leadSponsor=self.raw['protocolSection']['sponsorCollaboratorsModule']['leadSponsor']['name']
               self.briefSummary=self.raw['protocolSection']['descriptionModule']['briefSummary']
               self.status=self.raw['protocolSection']['statusModule']['overallStatus']

               
               
               self.sex=self.raw['protocolSection']['eligibilityModule']['sex']
               try:
                   self.phases=",".join(self.raw["protocolSection"]['designModule']['phases'])
               except:
                   self.phases=""

               #if 'armsInterventionsModule' in raw['protocolSection']:
               # if 'interventions' in raw['protocolSection']['armsInterventionsModule']:
               #    self.interventionName=self.collate(raw['protocolSection']['armsInterventionsModule']['interventions'],"name")
               
               self.interventionName=self.collate( self.getValueIfExists(['armsInterventionsModule', 'interventions'],
                                                 self.raw['protocolSection']), 'name')
               
               #Truncate to only 5 locations
               self.locationFacility=self.collate( self.getValueIfExists(['contactsLocationsModule', 'locations'], 
                                                 self.raw['protocolSection']), 'facility', 5)
               self.locationCity=self.collate(self.getValueIfExists(['contactsLocationsModule','locations'], 
                                                                    self.raw['protocolSection']), 'city', 5)
               
               
               
               self.primaryOutcomeMeasure=self.collate(self.getValueIfExists(['outcomesModule', 'primaryOutcomes'],
                                                                   self.raw['protocolSection']), "measure")
               
               #get summary of eligibility criteria
               with st.spinner('GPT is summarizing Inclusion/Exclusion Criteria for these studies...'):
                self.eligibilityCriteria=self.raw['protocolSection']['eligibilityModule']['eligibilityCriteria']
                #self.eligibilityCriteria=await getSummary(self.eligibilityCriteria) #Commenting this out as this does the summarization
                #Taking a short cut to get the first 1000 characters
                self.eligibilityCriteria=self.eligibilityCriteria[0:1000]
                #st.write(len(self.eligibilityCriteria))
                
                
           except Exception as e:
               st.write(f"Error in study data {self.nctid}, {e}")
               pass
               #st.write(raw)

class StudyDetail(Study):
 organizationName=""
 studyFullName=""
 startDate=""
 primaryCompleteDate=""
 studyFirstSubmitDate=""
 studyFirstSubmitQcDate=""
 studyFirstPostDateStruct=""
 lastUpdateSubmitDate=""
 lastUpdatePostDateStruct=""
 responsiblePartyName=""
 studyType=""
 studyDesignAllocation=""
 studyDesignInterventionModel=""
 studyDesignPrimaryPurpose=""
 studyDesignMasking=""
 studyDesignWhoMasked=""
 studyenrollmentCount=""
 secondaryOutcomes=""
 studyInterventionDescription=""

 def __init__(self,raw=""):
       Study.__init__(self,raw)


       

 async def getStudyDetail(self):
     
     #call process study
     try:
         
        await self.processStudy()
       
        self.organizationName=self.raw['protocolSection']['identificationModule']['organization']['fullName']
        self.studyFullName=self.raw['protocolSection']['identificationModule']['officialTitle']
        self.startDate=self.raw['protocolSection']['statusModule']['startDateStruct']['date']
        self.primaryCompleteDate=self.raw['protocolSection']['statusModule']['primaryCompletionDateStruct']['date']
        self.studyFirstSubmitDate=self.raw['protocolSection']['statusModule']['studyFirstSubmitDate']
        self.studyFirstSubmitQcDate=self.raw['protocolSection']['statusModule']['studyFirstSubmitQcDate']
        self.studyFirstPostDateStruct=self.raw['protocolSection']['statusModule']['studyFirstPostDateStruct']['date']
        self.lastUpdateSubmitDate=self.raw['protocolSection']['statusModule']['lastUpdateSubmitDate']
        self.lastUpdatePostDateStruct=self.raw['protocolSection']['statusModule']['lastUpdatePostDateStruct']['date']
        try:
            self.studyInterventionDescription=self.collate(self.getValueIfExists(['armsInterventionsModule','interventions'],
                                                           self.raw['protocolSection']), 'description')
        except:
            pass

        try:
            self.responsiblePartyName=self.raw['protocolSection']['sponsorCollaboratorsModule']['responsibleParty']['investigatorFullName']
        except:
            pass
        self.studyType=self.raw['protocolSection']['designModule']['studyType']
        self.studyDesignAllocation=self.raw['protocolSection']['designModule']['designInfo']['allocation']
        self.studyDesignAllocation=self.raw['protocolSection']['designModule']['designInfo']['interventionModel']
        try:
            self.studyDesignAllocation=self.raw['protocolSection']['designModule']['designInfo']['primaryPurpose']
        except:
            pass
        self.studyDesignMasking=self.raw['protocolSection']['designModule']['designInfo']['maskingInfo']['masking']
        try:
            self.studyDesignWhoMasked=", ".join(self.raw['protocolSection']['designModule']['designInfo']['maskingInfo']['whoMasked'])
        except:
            pass
        self.studyenrollmentCount=self.raw['protocolSection']['designModule']['enrollmentInfo']['count']
        try:
            self.secondaryOutcomes=self.raw['protocolSection']['outcomesModule']['secondaryOutcomes']
        except:
            pass

     except Exception as e:
        st.write(f"Error in getStudyDetaily {self.nctid}, {e}")    

 
 
 def getStudyDetailsJson(self):
    
    try:
      
        mydict=self.__dict__
        mydict.pop('raw')
        return mydict
        #write meaningful column names
        #df.columns=[camel_case_split(str(n)) for n in df.columns]
        #return df
    except Exception as e:
        st.write(f"Error in getStudyDetailDF {self.nctid}, {e}")
        return None
    



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
          
          #modern way to do it is below
          #tasks=list(asyncio.create_task(s.processStudy())  for s in self.studies)
          #result=await asyncio.gather(*tasks, return_exceptions=True)
          
          
          loop = asyncio.new_event_loop()
          asyncio.set_event_loop(loop)
          tasks=[loop.create_task(s.processStudy())  for s in self.studies]
          group = asyncio.gather(*tasks, return_exceptions=True)
          loop.run_until_complete(group) 
          loop.close()
           
          return self.response
      
      except HTTPError as err:
          st.write(f"HTTP error occured in Trials.getStudies(): {err}")
      except Exception as e:
          st.write(f"Error {e}")
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
    
  #returns studies as json
  def getStudiesAsJson(self):
    df=self.getStudiesAsDF()
    if df is not None:
        return df.to_json()
   
      

#endregion

#endregion
