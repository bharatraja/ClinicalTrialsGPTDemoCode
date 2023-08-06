import streamlit as st
import ClinicalTrialClasses as CT
import CTUtils as CTU
import asyncio
import openai
import os
import logging
import pandas as pd
import json 
import random
import time

def simpleOnclick(querystr) -> None:
      st.session_state['study_match_args']=querystr
      st.session_state['go_to_study_match'] =True




def initializeSessionVariables():
    if 'studyID' not in st.session_state:
        st.session_state['studyID']=""
    if 'study_match_args' not in st.session_state:
        st.session_state['study_match_args'] =""
    if 'go_to_study_match' not in st.session_state:
        st.session_state['go_to_study_match'] =False


def setStudyID():
    st.session_state['studyID']=st.session_state['study']

    

#region doMatch
async def doMatch(patient_id="", eligibility=""):
    
    patient=CT.Patient()
    result = await patient.getPatientDetails(patient_id)
    gpt_message=[]
    gpt_message.append(CTU.generate_system_prompt_for_match(eligibility, result.json()))
    gpt_message.append({"role":"user","content": "Is this patient a match for the study?"})
    try: 
        output=await CTU.getResponseFromGPT(gpt_message)
        if output is None:
             output="Sorry I cant determine a match"

    
        #output="Message from GPT"
    except Exception as e:
        output="Sorry I dont know the answer to that"
    return output        
#endregion


#region drawAllStudyMatches
async def drawAllStudyMatches():

    with st.sidebar:
       if st.session_state['df'] is not None:
            study=st.selectbox("Select Study ", 
                                list(st.session_state['df']['Nctid']),
                                   index=0)
            
            
            
            st.divider()
       else: 
            st.info("Enter a study id and get data", icon="ℹ️")
            study=st.text_input("Enter the Study ID (NCTID)", 
                                    placeholder="Example: NCTID", value=st.session_state['studyID'], 
                                    on_change=setStudyID, key="study")
            get_study= st.sidebar.button(label='Get Study')

    #Begin Main Window    
    st.subheader(f"Matches For Study - NCTID ({study})")


    #get study info especially eligibility Criteria
    if study != "":
        url=CT.TrialsQuery(study_id=str(study)).getStudyDetailQuery()
        r=CTU.getQueryResultsFromCTGov(url)
        if r.status_code == 200:
            studyDetail=CT.StudyDetail(r.json())
            await studyDetail.getStudyDetail()
            study_json=studyDetail.getStudyDetailsJson()
         
            #Get patient info
            patients=CT.Patient()
            j=(await patients.getAllPatients()).json()
            j=eval(j)
            

            
            df=pd.DataFrame.from_dict(j, orient='columns')
            
            #generate 10 random numbers from 1 to len(pateints records)
            rand_ints= [random.randint(0, len(df)) for p in range(0, 10)]
         
            #eligibility critera
            with st.expander("Eligibility Criteria"):
                st.info(study_json['eligibilityCriteria']) 


            #get the patient info for those 10 patients
            patient_tsk=[]
            for i in rand_ints:
                #patient_tsk.append(asyncio.to_thread(doMatch,df.iloc[i][0],study_json['eligibilityCriteria'] ))
                patient_tsk.append(asyncio.create_task(doMatch(df.iloc[i][0],
                                                               study_json['eligibilityCriteria'])))
               
            with st.spinner("Matching Patients..."):
             results=await asyncio.gather(*patient_tsk)
            i=0
            for r in results:
                st.button("Explore this match further!", on_click=simpleOnclick, 
                                 args=[f"studyid={study}&patientid={df.iloc[rand_ints[i]][0]}"], key=f"{time.time() * random.randint(0, 1000)}")
                st.info(f"Patient {df.iloc[rand_ints[i]][0]} \n\n  Match Status for the study: \n\n{r}")
                st.divider()
                i=i+1
                

            # for fin in asyncio.as_completed(patient_tsk, timeout=100):
            #         result=await fin
            #         st.button("I want to contribute!", on_click=simpleOnclick, 
            #                     args=[f"studyid=2000&patientid=1"], key=f"{time.time() * 1000}")

            #         st.info(f"Patient {df.iloc[i][0]} \n\n Match Status for the study: \n\n{result}")
                
        else:
            st.error(f"Error study id: {study} not found")
            return
    else:
         #No study id selected
        st.info("Enter a study id and get data", icon="ℹ️")
    

#endregion




async def main():
    
    initializeSessionVariables()

    if st.session_state['go_to_study_match']:
        st.session_state['go_to_study_match'] =False
        CTU.switch_page("Study Match", st.session_state['study_match_args'])

    st.set_page_config(page_title="Clinical Trials Companion",  page_icon=":robot_face:", layout="wide")
    CTU.hideStreamlitStyle()
    st.title(":robot_face: Clinical Trials Demo GPT Companion")


    await drawAllStudyMatches()        

if __name__=="__main__":
    asyncio.run(main())