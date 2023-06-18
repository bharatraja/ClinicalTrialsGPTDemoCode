import asyncio


async def function_asyc():
	for i in range(100000):
		if i % 20000 == 0:
			print("Hello, I'm Abhishek")
			print("GFG is Great")
			await asyncio.sleep(0.054)
			
	return 100

async def function_2():
	print("\n HELLO WORLD \n")
	return 0

async def main():
	i=0
	f1 = loop.create_task(function_asyc())
	f2 = loop.create_task(function_2())
	await asyncio.wait([f1, f2])
	print(f1.result())
    

# to run the above function we'll
# use Event Loops these are low
# level functions to run async functions
loop = asyncio.get_event_loop()
f1=loop.create_task(function_asyc())
f2=loop.create_task(function_2())
print("Here 1")
loop.run_until_complete(asyncio.wait([f1, f2]))
print("Here 2")
print(f1.result())
#loop.run_until_complete(function_asyc())
loop.close()

# You can also use High Level functions Like:
# asyncio.run(function_asyc())
