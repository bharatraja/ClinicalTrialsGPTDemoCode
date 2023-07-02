import streamlit as st
from streamlit.source_util import get_pages
import ClinicalTrialClasses as CT
import asyncio
from tenacity import retry, wait_random_exponential, stop_after_attempt 
import openai
from streamlit_chat import message
import os


def clearOnChange():
    st.session_state['refreshChat'] = True
    
    

def generate_system_prompt_gpt(data=""):
    return [{"role":"system","content": f"""You are an AI assistant that answers questions on Clinical trials studies information provided as json below:
                {data}                
                """}]

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
async def generate_study_detail_output(user_input=""):
    
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

    
          
async def main():
    st.set_page_config(page_title="Clinical Trials Companion",  page_icon=":robot_face:", layout="wide")
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
    st.title(":robot_face: Clinical Trials Demo GPT Companion")

    initializeSessionVariables()
    
    
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
        r=CT.getQueryResultsFromCTGov(url)
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
        with st.expander(f"No of PubMed Aticles: {len(studyDetail.pubmedArticles)}", expanded=False):
            for article in studyDetail.pubmedArticles:
                st.info(f"""Article Title: {article['title']} \n\n Article PubMed ID: {article['pubmed_id']}\n\n Results: - {article['results']} \n\n Go to Article: https://pubmed.ncbi.nlm.nih.gov/{article['pubmed_id']}/""")
                            
            
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
            

        
    

if __name__=="__main__":
    asyncio.run(main())