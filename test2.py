# telnetdemo.py
import asyncio
from asyncio import StreamReader, StreamWriter

async def echo(reader: StreamReader, writer: StreamWriter): 
    print('New connection.')
    try:
        while data := await reader.readline():  
            writer.write(data.upper())  
            await writer.drain()
        print('Leaving Connection.')
    except asyncio.CancelledError:  
        print('Connection dropped!')

async def main(host='127.0.0.1', port=8888):
    server = await asyncio.start_server(echo, host, port) 
    async with server:
        await server.serve_forever()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print('Bye!')
    


# alltaskscomplete.py
import asyncio

async def f(delay):
    await asyncio.sleep(1 / delay)  
    return delay

loop = asyncio.get_event_loop()
for i in range(10):
    loop.create_task(f(i))
pending = asyncio.all_tasks()
group = asyncio.gather(*pending, return_exceptions=True)
results = loop.run_until_complete(group)
print(f'Results: {results}')
loop.close()