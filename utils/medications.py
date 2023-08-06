import asyncpg
import asyncio
from typing import List, Tuple, Union
from random import sample
import time
import utils.shared as U
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from asyncpg.pool import Pool



class Medication():
    
    def init(self): 
        pass

    def init(self, condition_id: int=0, patient_id:str="", encounter_id: str="", 
             allergy_name: str="", allergy_description: str=""):
        self.id = condition_id

    @staticmethod
    async def getMedicationsForPatient(request:Request):
        
        
        #connect to db
        conn= U.getConnection(request)
        conditions: List[asyncpg.Record]=await conn.fetch('SELECT * FROM medications WHERE patient=$1', request.match_info['id'])
        a=[]
        for row in conditions:
            a.append('"' + row['description'].strip() + ", " +  row['reasondescription'].strip() +' ( from- ' + str(row['start']) + ", to- " + str(row['stop']) + ')"')
        
        str1= '"Medications": [' + ', '.join(set(a)) + "]"
        return str1

async def main():
    await Medication.getMedicationsForPatient("b9c610cd-28a6-4636-ccb6-c7a0d2a4cb85")
    


if __name__ == "__main__":
    asyncio.run(main())



        
    

