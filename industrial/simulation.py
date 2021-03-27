import time
import random
import datetime
import time

from industrial.database import db_session, Machine, MachineData
from industrial.constants import SIM_SLEEP_TIME, RESOLVE_STEPS

DELAY = float(1)

class Simulation:
    started = False
    store = False
    danger_mode = False

    def __init__(self, sector_id):
        self.sector_id = sector_id
        machines_objs = Machine.query.filter(Machine.sector_id == self.sector_id).all()

        self.machines = {}
        for m in machines_objs:
            self.machines[m.id] = {
                "in_danger": False,
                "last_data": [],
                "value_in_danger": 0,
                "current_danger_message": 0
            }
        db_session.commit()
        print(self.machines)

    def start(self, store=False):
        self.started = True

        #TODO: check for refreshing object (refresh state)
        while(self.started):
            start = time.time()

            if store:
                # store mode
                machines = Machine.query.filter(Machine.started == True).all()
                print(len(machines))
                
                for m in machines:
                    self.generate_and_store(m)
                
                time.sleep(SIM_SLEEP_TIME)
                db_session.commit()

            for m in self.machines:
                self.machines[m]["last_data"] = self.generate(m)
                print(m, self.machines[m]['last_data'])
            
            elapsed = time.time() - start

            time.sleep(DELAY - elapsed)

            
        db_session.remove()

    def set_danger_mode(self, machine_id):
        if int(machine_id) not in self.machines:
            return False
            
        self.danger_mode = True
        self.machines[int(machine_id)]["in_danger"] = True
        self.machines[int(machine_id)]["value_in_danger"] = random.randint(1,3)
        print(self.machines)
        return True

    def get_danger_instruction_message(self, machine_id):
        message = None
        user_id = None

        if not self.machines[int(machine_id)]["in_danger"]:
            message = ""
        elif self.machines[int(machine_id)]["current_danger_message"] == len(RESOLVE_STEPS):
            self.machines[int(machine_id)]["current_danger_message"] = 0
            self.resolve_danger_mode(machine_id)
            message = "All procedures completed."
        else:
            message = RESOLVE_STEPS[self.machines[int(machine_id)]["current_danger_message"]]

            if self.machines[int(machine_id)]["current_danger_message"] == 1:
                user_id = 3
            if self.machines[int(machine_id)]["current_danger_message"] == 3:
                user_id = 2

            self.machines[int(machine_id)]["current_danger_message"] += 1

        return message, user_id

    def resolve_danger_mode(self, machine_id):
        self.danger_mode = False
        self.machines[int(machine_id)]["in_danger"] = True
        self.machines[int(machine_id)]["value_in_danger"] = None

        return True

    def generate_and_store(self, machine):
        values = self.generate()

        new_data = MachineData(machine=machine, 
            value1=values[0], value2=values[1], value3=values[2], timestamp=datetime.datetime.now())
        db_session.add(new_data)

    def generate(self, machine_id):
        in_danger = self.machines[int(machine_id)]['in_danger']
        value_in_danger = self.machines[int(machine_id)]['value_in_danger']


        # value 1: speed RPM [0:3000]
        if(in_danger and value_in_danger == 1):
            value1 = random.randint(4000, 5000)
        else:
            value1 = random.randint(2500,3000)

        # value 2: efficiency [0:100]
        if(in_danger and value_in_danger==2):
            value2 = random.randint(0, 30)
        else:
            value2 = random.randint(95, 100)

        # value 3: temperature [0:100]
        if(in_danger and value_in_danger == 3):
            value3 = random.randint(70,80)
        else:
            value3 = random.randint(40, 43)

        return [value1, value2, value3]

if __name__ == "__main__":

    sim = Simulation(1)
    # sim.start()
    print(sim.generate(1))