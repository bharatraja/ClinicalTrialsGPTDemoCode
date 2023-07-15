import streamlit as st
from streamlit.source_util import get_pages
import ClinicalTrialClasses as CT
import CTUtils as CTU
import asyncio
import openai
from streamlit_chat import message
import os
import logging
import pandas as pd
import json 

def clearOnChange():
    st.session_state['refreshChat'] = True
    

def generate_system_prompt_gpt(data=""):
    return [{"role":"system","content": f"""You are an AI assistant that answers questions on Clinical trials studies information provided as json below:
                {data}                
                """}]


def generate_system_prompt_for_match(trial_eligibility="", patient_info=""):
    
    #j1=json.loads(patient_info)
    content='"You are an AI assistant that evaluates if a patient is eligibile for a given clinincal trial enrollment. Provided below is both the eligibility criteria for the study and patient information. Using this information you recommend if the patient is a potential match for the study. If a patient meets some of the critieria you can say a potential match and recommend additional areas of investigation. Clinical Trial Eligibility Criteria: '
    content += "\n\n" +  trial_eligibility + "Patient Information: \n\n" + json.dumps(patient_info) + '"}'

    return{"role":"system","content": f"{content}"}
    

async def generate_study_detail_output(user_input=""):
    return await CTU.getResponseFromGPT(st.session_state['messages'])
    
def initializeSessionVariables():
     #region Session State
    if 'studyDetailPageVisited' not in st.session_state:
        if 'homePageVisited' in st.session_state:
            if 'refreshChat' in st.session_state:
                st.session_state['refreshChat']=True

            #delete studyDetailPageVisited
            del st.session_state['homePageVisited']
        
        #create the fact they visited
        st.session_state['studyDetailPageVisited']=True


    if 'messages' not in st.session_state:
        st.session_state['messages'] =[]
    if 'df' not in st.session_state:
        st.session_state['df']=None
    if 'json' not in st.session_state:
        st.session_state['json']=None
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []
    if 'past' not in st.session_state:
        st.session_state['past'] = []
    if 'refreshChat' not in st.session_state:
        st.session_state['refreshChat'] = False
    #endregion

#region drawStudyDetail
async def drawStudyDetail():

    with st.sidebar:
       if st.session_state['df'] is not None:
            study=st.selectbox("Select Study ", 
                                list(st.session_state['df']['Nctid']),
                                   index=0,
                                   on_change=clearOnChange)
            
            
            
            st.divider()
       else: 
            st.info("Enter a study id and get data", icon="ℹ️")
            study=st.text_input("Enter the Study ID (NCTID)", 
                                    placeholder="Example: NCTID")
            get_study= st.sidebar.button(label='Get Study')



    #Begin Main Window    
    st.subheader(f"Study Detail - NCTID ({study})")
   
    if study != "":
        url=CT.TrialsQuery(study_id=str(study)).getStudyDetailQuery()
        #st.write(url)
        r=CTU.getQueryResultsFromCTGov(url)
        if r.status_code == 200:
            studyDetail=CT.StudyDetail(r.json())
            await studyDetail.getStudyDetail()
            st.session_state['json']=studyDetail.getStudyDetailsJson()
            st.session_state['messages']=generate_system_prompt_gpt(st.session_state['json'])
        else:
            study=""

        
    #main form
    if st.session_state['refreshChat']:
        st.session_state['generated'] = []
        st.session_state['past'] = []
        st.session_state['messages'] = []
        st.session_state['messages']=generate_system_prompt_gpt(st.session_state['json'])
        st.session_state['refreshChat']=False


    if (st.session_state['df'] is not None) or study != "": 
        st.info("Now that you have data, you can ask questions of it and GPT Companion will answer them for you", icon="ℹ️")
        st.info(f"Study Title: {studyDetail.briefTitle} ")
        st.info(f"Brief Summary:{studyDetail.briefSummary}")
        if studyDetail.pubmedArticles is not None:
            with st.expander(f"No of PubMed Articles: {len(studyDetail.pubmedArticles)}", expanded=False):
                for article in studyDetail.pubmedArticles:
                    st.info(f"""Article Title: {article['title']} \n\n Article PubMed ID: {article['pubmed_id']}\n\n Pub Date: {article['publication_date']}\n\nAbstract:- {article['abstract']} \n\nMethods:- {article['methods']} \n\n Results: - {article['results']} \n\n Conclusions: - {article['conclusions']} \n\n Go to Article: https://pubmed.ncbi.nlm.nih.gov/{article['pubmed_id']}/""")
                                
            
        # container for chat history
        response_container = st.container()
        # container for text box
        container = st.container()

        with container:
            with st.form(key='my_form', clear_on_submit=True):
                user_input = st.text_area("You:", key='input', height=100)
                submit_button = st.form_submit_button(label='Send')
                clear_button = st.form_submit_button(label="Clear Conversation")


            if submit_button and user_input:
                with response_container:
                    

                    #Append the user input
                    st.session_state['past'].append(user_input)
                    st.session_state['messages'].append({"role": "user", "content": user_input})

                    
                    
                    with st.spinner('GPT Getting answers for you...'):
                        try: 
                            output=await generate_study_detail_output(user_input)

                        except Exception as e:
                            #pass
                            #st.write(e)
                            output="Sorry I dont know the answer to that"

                        #Append the out from model
                        st.session_state['generated'].append(output)
                    
                        st.session_state['messages'].append({"role": "assistant", "content": output})                #st.write(st.session_state['messages'])
                        st.session_state['refreshChat']=False

                # reset everything
            if clear_button:
                st.session_state['generated'] = []
                st.session_state['past'] = []
                st.session_state['messages'] = []
                st.session_state['messages']=generate_system_prompt_gpt(st.session_state['json'])

            if st.session_state['generated']:
                with response_container:
                    for i in range(len(st.session_state['generated'])):
                        message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
                        message(st.session_state["generated"][i], key=str(i))
#endregion


#region drawPatientInfo
async def drawPatientInfo():

    patients=CT.Patient()
    j=(await patients.getAllPatients()).json()
    j=eval(j)
    #st.write(j)
    df=pd.DataFrame.from_dict(j, orient='columns')
    #st.write(df)
    
    
    st.subheader("Patient List")
    patient=st.selectbox("[id, birthdate, deathdate, martial status, race, ethnicity, gender]", 
                                list(df['id'] + "," +  df['birthdate'] + ',' + df['deathdate'] + ',' + df['marital'] + ',' + df['race']
                                     + ", " + df['ethnicity'] + ", " + df['gender']),
                                   index=0)
        
    cols3,cols4=st.columns([1,2])
    with cols3:
        search_all=st.button("Match All")
    with cols4:
        search_selected=st.button("Match Selected")   

    st.write(search_selected)           

    if search_selected:
        #get patient detail
        patient_detail=(await patients.getPatientDetails(patient.split(",")[0])).json()
        study_info=st.session_state['json']['eligibilityCriteria']
       
        gpt_prompt_for_match=generate_system_prompt_for_match(study_info, patient_detail)
               
        #Call GPT to match the patient
        #Append the user input
        st.session_state['past']=[]
        st.session_state['messages']=[]
        st.session_state["generated"]=[]
        
        st.session_state['past'].append("Generting Patient Match")
        st.session_state['messages'].append(gpt_prompt_for_match)
        st.session_state['messages'].append({"role": "user", "content": "is the user a match?"})
        #st.write(type(st.session_state['messages']))
        #st.write(st.session_state['messages'])
                    
                    
        with st.spinner('GPT Getting answers for you...'):
            try: 
                output=await CTU.getResponseFromGPT(st.session_state['messages'])

            except Exception as e:
                            #pass
                            #st.write(e)
                output="Sorry I dont know the answer to that"

        #Append the out from model
        st.session_state['generated'].append(output)
        st.session_state['messages'].append({"role": "assistant", "content": output})                #st.write(st.session_state['messages'])
        st.session_state['refreshChat']=False
        
         

    #region PatientDetail    
    if patient != "":
        selected_patient=patient.split(",")[0]
        #get the patient detail
        patient_detail=(await patients.getPatientDetails(selected_patient))
        #patient_detail=requests.get("http://127.0.0.1:8080/patients/217f95a3-4e10-bd5d-fb67-0cfb5e8ba075")
        if patient_detail is not None:
            patient_detail=patient_detail.json()
            summary_info="Patient Summary  \n"
            with st.expander(f"{summary_info}", expanded=True):
                summary_info=f"Race: {patient_detail['race']}  \n"
                summary_info+=f"Birth Date: {patient_detail['birthdate']}  \n"
                summary_info+=f"Death Date: {patient_detail['deathdate']}  \n"
                summary_info+=f"Marital Status: {patient_detail['marital']}  \n"
                summary_info+=f"Ethnicity: {patient_detail['ethnicity']}  \n"
                summary_info+=f"Gender: {patient_detail['gender']}  \n"
                st.info(summary_info)

            allergy_info="Allergies  \n"
            with st.expander(f"{allergy_info}", expanded=False):
                    allergy_info=','.join(patient_detail['Allergies'])
                    st.info(allergy_info)
                
            conditions_info="Conditions  \n"
            with st.expander(f"{conditions_info}", expanded=False):
                    conditions_info=','.join(patient_detail['Conditions'])
                    st.info(conditions_info)

            careplans_info="Care Plans  \n"
            with st.expander(f"{careplans_info}", expanded=False):
                    careplans_info=','.join(patient_detail['Careplan'])
                    st.info(careplans_info)

            devices_info="Devices  \n"
            with st.expander(f"{devices_info}", expanded=False):
                    devices_info=','.join(patient_detail['Devices'])
                    st.info(devices_info)

            encounters_info="Encounters  \n"
            with st.expander(f"{encounters_info}", expanded=False):
                    encounters_info=','.join(patient_detail['Encounters'])
                    st.info(encounters_info)

            immunizations_info="Immunizations  \n"
            with st.expander(f"{immunizations_info}", expanded=False):
                    immunizations_info=','.join(patient_detail['Immunizations'])
                    st.info(immunizations_info)

            medications_info="Medications  \n"
            with st.expander(f"{medications_info}", expanded=False):
                    medications_info=','.join(patient_detail['Medications'])
                    st.info(medications_info)
    #endregion



#endregion
          


async def main():
    st.set_page_config(page_title="Clinical Trials Companion",  page_icon=":robot_face:", layout="wide")
    CTU.hideStreamlitStyle()
    st.title(":robot_face: Clinical Trials Demo GPT Companion")


    initializeSessionVariables()
    
    col1, col2=st.columns([3,1])
    with col2:
        await drawPatientInfo()   
    with col1:
        await drawStudyDetail()
          

if __name__=="__main__":
    asyncio.run(main())