import threading
from queue import Queue

class ThreadBot(threading.Thread):  
  def __init__(self, kit=None):
    super().__init__(target=self.manage_table,)  
    self.cutlery = Cutlery(knives=0, forks=0)  
    self.tasks = Queue()
    self.kitchen=kit

  def manage_table(self):
    while True:  
      task = self.tasks.get()
      if task == 'prepare table':
        self.kitchen.give(to=self.cutlery, knives=4, forks=4) 
        #print(self.kitchen)
      elif task == 'clear table':
        self.cutlery.give(to=self.kitchen, knives=4, forks=4)
        #print(self.kitchen)
      elif task == 'shutdown':
        return
      

from attr import attrs, attrib

@attrs  
class Cutlery:
    knives = attrib(default=0)  
    forks = attrib(default=0)
    lock:threading.Lock=attrib(default=threading.Lock())

    def give(self, to: 'Cutlery', knives=0, forks=0):  
        self.change(-knives, -forks)
        to.change(knives, forks)

    def change(self, knives, forks):  
            with self.lock:
                self.knives += knives
                self.forks += forks

kitchen = Cutlery(knives=100, forks=100)  
bots = [ThreadBot(kitchen) for i in range(10)]  

import sys
for bot in bots:
    for i in range(int(sys.argv[1])):  
        bot.tasks.put('prepare table')
        bot.tasks.put('clear table')
    bot.tasks.put('shutdown')  

print('Kitchen inventory before service:', kitchen)
for bot in bots:
    bot.start()
    #bot.join()

name=input('what is your name: ')
print('kitchen inventory after services: ', kitchen)

