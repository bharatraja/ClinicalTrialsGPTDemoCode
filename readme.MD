# Clininical Trials Demo
Clinical Trials Demo is used to show the power of GPT when used with Clinical Trials data. This application pulls data from ClinicalTrials.gov using the beta api. Once we have the data, I show two ways we can use a GPT Copilot/Companion experience to ask questions of that particular data.

The UI for this application is built with Streamlit. The backend data is a from Synthea a synthetic data source. The assumption is you will have your own patient data store that you can query and pull data from. 


# Architecture
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
CT_GOV_API_BASE='https://beta.clinicaltrials.gov/api/v2'
PATIENT_DB_URL='url of the web app endpoint for your patient api'

For the Patients DB Web App you need the following environmental variables
SYNTHEA_DB_HOST='location of your postreg db'
SYNTHEA_DB_NAME='name of your database'
SYNTHEA_DB_PASSWORD='db password'
SYNTHEA_DB_POOL_MAX_SIZE=6
SYNTHEA_DB_POOL_MIN_SIZE=6
SYNTHEA_DB_PORT=5432
SYNTHEA_DB_USER='db user name'

# Start up commands
To start your web app in Azure Web App do the following
 python -m streamlit run ClinicalTrials.py --server.port 8000 --server.address 0.0.0.0

To start the api server
 python patients.py --server.port 8000 --server.address 0.0.0.0



# Requirements.txt 
Contains all the modules you need to install
