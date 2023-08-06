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



class Allergy():
    
    def init(self): 
        pass

    def init(self, allergy_id: int=0, patient_id:str="", encounter_id: str="", 
             allergy_name: str="", allergy_description: str=""):
        self.id = allergy_id
        self.name = allergy_name
        self.description = allergy_description

    @staticmethod
    async def getAllergiesForPatient(request:Request) -> List['Allergy']:
        
        
        #connect to db
        conn= U.getConnection(request)
        allergies: List[asyncpg.Record]=await conn.fetch('SELECT * FROM allergies WHERE patient=$1', request.match_info['id'])
        a=[]
        for row in allergies:
            a.append('"' + row['type'] + '"')
        return '"Allergies": [' + ', '.join(set(a)) + "]"

async def main():
    await Allergy.getAllergiesForPatient("b9c610cd-28a6-4636-ccb6-c7a0d2a4cb85")
    


if __name__ == "__main__":
    asyncio.run(main())



        
    

