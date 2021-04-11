import os
import json

from industrial.database import *

def populate():
    abs_path = os.path.abspath(__file__)
    folder = os.path.dirname(os.path.dirname(abs_path))
    print(folder)
    with open(f"{folder}/industrial/json/population.json") as fp:
        population = json.load(fp)

    for area in population['areas']:
        check_area = Area.query.filter(Area.name == area['name']).first()
        if not check_area:
            new_area = Area(name=area['name'])
            db_session.add(new_area)
        else:
            new_area = check_area

        for sector in population['sectors']:
            if sector['area'] == new_area.name:
                check_sector = Sector.query.filter(Sector.name == sector['name']).first()
                if not check_sector:
                    new_sector = Sector(name=sector["name"], area=new_area)
                    db_session.add(new_sector)
                else:
                    new_sector = check_sector
                    
                for machine in population["machines"]:
                    if machine["sector"] == new_sector.name:
                        check_machine = Machine.query.filter(Machine.name == machine['name']).first()
                        if not check_machine:
                            new_machine = Machine(name=machine["name"], sector=new_sector)
                            db_session.add(new_machine)


    for u in population['users']:
        check_user = User.query.filter(User.name==u['name']).first()
        if check_user:
            continue

        user = User(name=u['name'], role=u['role'], phone=u['phone'])
        try:
            db_session.add(user)
        except Exception as e:
            print(e)
            continue

    db_session.commit()

    db_session.remove()

if __name__ == "__main__":
    populate()
