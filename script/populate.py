import os
import json

from app.database import *

def populate():
    abs_path = os.path.abspath(__file__)
    folder = os.path.dirname(os.path.dirname(abs_path))
    print(folder)
    with open(f"{folder}/app/json/population.json") as fp:
        population = json.load(fp)

    for area in population['areas']:
        new_area = Area(name=area['name'])
        db_session.add(new_area)

        for sector in population['sectors']:
            if sector['area'] == new_area.name:
                new_sector = Sector(name=sector["name"], area=new_area)
                db_session.add(new_sector)

                for machine in population["machines"]:
                    if machine["sector"] == new_sector.name:
                        new_machine = Machine(name=machine["name"], sector=new_sector)
                        db_session.add(new_machine)

    db_session.commit()

    db_session.remove()

if __name__ == "__main__":
    populate()
