import time
import random
import datetime

from app.database import db_session, Machine, MachineData
from app.constants import SIM_SLEEP_TIME


class Simulation:

    def __init__(self):
        self.started = False

    def start(self):
        self.started = True

        #TODO: check for refreshing object (refresh state)

        while(self.started):
            machines = Machine.query.filter(Machine.started == True).all()
            print(len(machines))
            
            for m in machines:
                self.generate_data(m)
            
            time.sleep(SIM_SLEEP_TIME)
            db_session.commit()
        db_session.remove()


    def generate_data(self, machine):
        rand1 = random.randint(0, 255)
        rand2 = random.randint(0, 255)
        rand3 = random.randint(0, 255)

        new_data = MachineData(machine=machine, 
            value1=rand1, value2=rand2, value3=rand3, timestamp=datetime.datetime.now())
        db_session.add(new_data)



if __name__ == "__main__":

    sim = Simulation()
    sim.start()