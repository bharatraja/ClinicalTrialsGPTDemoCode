import asyncpg
from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from aiohttp.web_response import Response,  json_response
from asyncpg import Record
from asyncpg.pool import Pool
from typing import List, Dict
import utils as U
import json
import datetime
from json import JSONEncoder
import os


class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()

routes=web.RouteTableDef()

@routes.get('/patients/{id}')
async def main(request: Request)->Response:

    conn=U.shared.getConnection(request)
    patient_id=request.match_info['id']#'217f95a3-4e10-bd5d-fb67-0cfb5e8ba075'
    #print(f"Patient Id is={patient_id}")
    patients: List[asyncpg.Record]=await conn.fetch('SELECT * FROM patients where id=$1', patient_id)
    patient_info=[]
    for row in patients:
        patient_info.append('"race": "' + row['race'] + '"')
        patient_info.append('"ethnicity": "' + row['ethnicity'] + '"')
        patient_info.append('"gender": "'+ row['gender'] + '"')
        patient_info.append('"birthdate": "' + str(row['birthdate']) + '"')
        patient_info.append('"deathdate": "' + str(row['deathdate']) + '"')
        patient_info.append('"marital": "' + str(row['marital']) + '"')
    
    patient_data='{ ' + ', '.join(patient_info) + ', \n'
    patient_data+=await U.Allergy.getAllergiesForPatient(request) + ", \n "
    patient_data+=await U.Condition.getConditionsForPatient(request) + ", \n "
    
    patient_data+=await U.CarePlan.getCareplanssForPatient(request) + ", \n"
    patient_data+=await U.Devices.getDevicesForPatient(request) + ", \n"
    patient_data+=await U.Encounter.getEncountersForPatient(request) + ", \n"
    patient_data+=await U.Immunization.getImmunizationsForPatient(request) + ", \n"
    patient_data+=await U.Observation.getObervationsForPatient(request) + ", \n"
    patient_data+=await U.Medication.getMedicationsForPatient(request) + "}"
    #print(patient_data)
    
    j=json.loads(patient_data)
    return json_response(j)
    # with open('data.json', 'w') as outfile:
    #     json.dump(j, outfile)

@routes.get('/patients')
async def getPatients(request:Request)->Response:
    conn=U.shared.getConnection(request)
    patients: List[asyncpg.Record]=await conn.fetch('SELECT * FROM patients')
    #print(len(patients))
    patient_info="["
    for row in patients:
        patient_info+='{ "id": "' + row['id'] + '", ' 
        patient_info+=' "birthdate": "' + str(row['birthdate']) + '", '
        patient_info+=' "deathdate": "' + str(row['deathdate']) + '", '
        patient_info+=' "marital": "' + row['marital'] + '", '
        patient_info+=' "race": "' + row['race'] + '", '
        patient_info+=' "ethnicity": "' + row['ethnicity'] + '", '
        patient_info+=' "gender": "' + row['gender'] + '", '
        patient_info+=' "healthcare_coverage": "' + str(row['healthcare_coverage']) + '"},'

    patient_info=patient_info[:-1]
    patient_info+="]"     
    # result_as_dict: List[Dict] = [dict(brand) for brand in patients]
    # j=json.dumps(result_as_dict, cls=DateTimeEncoder)
    return web.json_response(patient_info)

    
@routes.get('/')
async def hello(request: Request)->Response:
    return web.Response(text="Hello, World")
# if __name__ == "__main__":
#     asyncio.run(main()) 

app=web.Application()
app.add_routes(routes)
app.on_startup.append(U.create_database_pool)                
app.on_cleanup.append(U.destroy_database_pool)

web.run_app(app, port=8000)
