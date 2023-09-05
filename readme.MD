# Clininical Trials Demo
Clinical Trials Demo is used to show the power of GPT when used with Clinical Trials data. This application pulls data from ClinicalTrials.gov using the beta api. Once we have the data, I show two ways we can use a GPT Copilot/Companion experience to ask questions of that particular data

#Architecture
The application has the following parts:

1. The UI code is written in Streamlit (ClinicalTrials.py is the main entry point). The UI code is hosted in an azure web app The UI code is captured in the following files and folders:
   - ClinicalTrials.py, CTUtils.py, ClinicalTrialClasses.py
   - pages & utils folder
2. The patient database is hosted on Azure PostgresSQL instance. patients.py is hosted in a seperate web app. 
3. You need a LLM deployed on Azure Open AI (GPT 3.5 Turbo 32K is the LLM model behind this code)

# Environmental Variables to Configure the application
For the UI WebApp you need the following environmental variables configured 

OPENAI_API_BASE='BASE OF YOUR AZURE OPEN AI API'<br>
OPENAI_API_KEY='YOUR API KEY'<br>
OPENAI_API_TYPE='azure'<br>
OPENAI_API_VERSION='2023-03-15-preview'<br>
OPENAI_API_CHAT_COMPLETION='your azure chat deployment name'<br>
GPT_DEMO_MAX_RECORDS_TO_RETURN=5<br>


# Requirements.txt 
Contains all the modules you need to install
