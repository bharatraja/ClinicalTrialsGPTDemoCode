import os
from time import sleep
from threading import Thread
# threads = [
#   Thread(target=lambda: sleep(60)) for i in range(10000)
# ]
# [t.start() for t in threads]
# print(f'PID = {os.getpid()}')
# [t.join() for t in threads]

# import os
# import threading
 
# print(f'Python process running with process id: {os.getpid()}')
# total_threads = threading.active_count()
# thread_name = threading.current_thread().name
 
# print(f'Python is currently running {total_threads} thread(s)')
# print(f'The current thread is {thread_name}')

# import threading
 
 
# def hello_from_thread():
#     print(f'Hello from thread {threading.current_thread()}!')
 
 
# hello_thread = threading.Thread(target=hello_from_thread)
# hello_thread.start()
 
# total_threads = threading.active_count()
# thread_name = threading.current_thread().name
 
# print(f'Python is currently running {total_threads} thread(s)')
# print(f'The current thread is {thread_name}')
 
# hello_thread.join()
# import multiprocessing
# import os
 
 
# def hello_from_process():
#     print(f'Hello from child process {os.getpid()}!')
# if __name__ == '__main__':
#     hello_process = multiprocessing.Process(target=hello_from_process)
#     hello_process.start()
 
#     print(f'Hello from parent process {os.getpid()}')
 
#     hello_process.join()
# from time import sleep
# from threading import Thread
 
# # custom thread
# class CustomThread(Thread):
#     # constructor
#     def __init__(self):
#         # execute the base constructor
#         Thread.__init__(self)
#         # set a default value
#         self.value = None
 
#     # function executed in a new thread
#     def run(self):
#         # block for a moment
#         sleep(1)
#         # store data in an instance variable
#         self.value = 'Hello from a new thread'
 
# # create a new thread
# thread = CustomThread()
# # start the thread
# thread.start()
# # wait for the thread to finish
# thread.join()
# # get the value returned from the thread
# data = thread.value
# print(data)
# print(input("Say something:"))
# print("Goodbye")import asyncio

import asyncio
import time
 
async def delay(delay_seconds: int) -> int:
    print(f'sleeping for {delay_seconds} second(s)')
    await asyncio.sleep(delay_seconds)
    print(f'finished sleeping for {delay_seconds} second(s)')
    return delay_seconds

# async def main():
    
#     # sleep_for_three = asyncio.create_task(delay(3))
#     # sleep_again = asyncio.create_task(delay(3))
#     # sleep_once_more = asyncio.create_task(delay(3))

#     sleep_for_three = delay(3)
#     sleep_again = delay(3)
#     sleep_once_more = delay(3)
   

#     start_t=time.time()
#     await sleep_for_three
#     await sleep_again
#     await sleep_once_more
#     stop_t=time.time()
#     print(start_t - stop_t)
 
# asyncio.run(main())
import functools
import time
from typing import Callable, Any
 
 
def async_timed():
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            print(f'starting {func} with args {args} {kwargs}')
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f'finished {func} in {total:.4f} second(s)')
 
        return wrapped
 
    return wrapper

import asyncio
 
@async_timed()
async def delay(delay_seconds: int) -> int:
    print(f'sleeping for {delay_seconds} second(s)')
    await asyncio.sleep(delay_seconds)
    print(f'finished sleeping for {delay_seconds} second(s)')
    return delay_seconds
 
 
@async_timed()
async def main():
    task_one = asyncio.create_task(delay(2))
    task_two = asyncio.create_task(delay(3))
    
    await task_one
    await task_two
 
 
asyncio.run(main())

