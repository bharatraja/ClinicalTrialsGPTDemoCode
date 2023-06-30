# Clininical Trials Demo
Clinical Trials Demo is used to show the power of GPT when used with Clinical Trials data. This application pulls data from ClinicalTrials.gov using the beta api. Once we have the data, I show two ways we can use a GPT Copilot/Companion experience to ask questions of that particular data

## Using GPT Directly
The first way is to use GPT directly and ask questions of the data. To do this, we create a JSON of the CT data and send it to GPT as part of the system prompt and then asks questions.

## Using Langchain Dataframe agent
Another way to do it is to convert the data from CT website to a pandas dataframe and use the dataframe to create a Langchain Pandas dataframe agent. Then the agent uses GPT in the backend.



# Environmental Variables to Configure the application
OPENAI_API_BASE='BASE OF YOUR AZURE OPEN AI API'<br>
OPENAI_API_KEY='YOUR API KEY'<br>
OPENAI_API_TYPE='azure'<br>
OPENAI_API_VERSION='2023-03-15-preview'<br>
OPENAI_API_CHAT_COMPLETION='your azure chat deployment name'<br>
GPT_DEMO_MAX_RECORDS_TO_RETURN=5<br>


# Requirements.txt 
Contains all the modules you need
