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
from time import sleep
from threading import Thread
 
# custom thread
class CustomThread(Thread):
    # constructor
    def __init__(self):
        # execute the base constructor
        Thread.__init__(self)
        # set a default value
        self.value = None
 
    # function executed in a new thread
    def run(self):
        # block for a moment
        sleep(1)
        # store data in an instance variable
        self.value = 'Hello from a new thread'
 
# create a new thread
thread = CustomThread()
# start the thread
thread.start()
# wait for the thread to finish
thread.join()
# get the value returned from the thread
data = thread.value
print(data)
print(input("Say something:"))
print("Goodbye")