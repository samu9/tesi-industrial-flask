import random
import datetime
import logging

from flask import Flask, jsonify, send_from_directory

from industrial.database import db_session, Area, Sector, Machine, MachineData, User, MachineLog

from industrial.constants import MACHINE_START, MACHINE_STOP, MACHINE_PAUSE, MACHINE_RESUME, RESOLVE_STEPS
from industrial.simulation import Simulation

logging.basicConfig(format='%(asctime)s %(message)s', filename='industrial.log', level=logging.INFO)

def create_app():

    log = logging.getLogger(__name__)
    app = Flask(__name__ , static_url_path='/static')
    # app.config.from_envvar("AREA")
    app.config.from_mapping(
        AREA=1,
        SQLALCHEMY_DATABASE_URI="mysql+mysqldb://root:@localhost[:3306]/industrial",
        USER_IMG_DIR="static"
        )

    AREA_ID = 1
    SECTOR_ID = 1    

    sim = Simulation(SECTOR_ID)

    # @app.before_request
    # def simulation_status():
    #     print(sim.machines)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()


    @app.route('/user/<id>/img', methods=['GET'])
    def get_user_image(id):
        return send_from_directory(app.config['USER_IMG_DIR'], id + '.jpg')


    @app.route('/position', methods=['GET'])
    def get_position():
        return jsonify({
            "area_id": AREA_ID,
            "sector_id": SECTOR_ID
        })


    @app.route('/area')
    def get_areas():
        areas = Area.query.all()
        result = []
        for a in areas:
            result.append({
                "id": a.id,
                "name": a.name
            })
        return jsonify(result)
    

    @app.route('/area/<id>')
    def get_area_data(id):
        area = Area.query.filter(Area.id == id).first()
        result = {
            "id": area.id,
            "name": area.name,
            "sectors": len(area.sectors)
        }
        return jsonify(result)


    @app.route('/area/<area_id>/sectors')
    @app.route('/sector')
    def get_sectors(area_id=None):
        query = Sector.query
        sectors = query.all() if area_id is None \
            else query.filter(Sector.area_id==area_id).all()
        result = []
        for s in sectors:
            result.append({
                "id": s.id,
                "name": s.name
            })
        return jsonify(result)


    @app.route('/sector/<id>')
    def get_sector_data(id):
        sector = Sector.query.filter(Sector.id == id).first()
        result = {
            "id": sector.id,
            "name": sector.name,
            "machines": len(sector.machines)
        }
        return jsonify(result)


    @app.route('/sector/<sector_id>/machines')
    @app.route('/machine')
    def get_machines(sector_id=None):
        query = Machine.query

        machines = query.all() if sector_id is None \
            else query.filter(Machine.sector_id==sector_id).all()
        result = []
        for m in machines:
            result.append({
                "id": m.id,
                "name": m.name,
                "status": m.status,
                "temp_threshold": 60,
                "speed_threshold": 3500,
                "efficiency_threshold": 60,
                "value_in_danger": None
            })
        return jsonify(result)


    @app.route("/machine/<id>/danger", methods=['POST'])
    def set_in_danger(id):
        sim.set_danger_mode(id)
        return jsonify({"message": "Danger set", "result": True})


    @app.route("/machine/<id>/danger/instruction", methods=['GET'])
    def get_danger_instructions(id):
        message, user_id = sim.get_danger_instruction_message(id)

        result = {
            "message": message
        }

        if user_id is not None:
            assistant = User.query.filter(User.id == user_id).first()

            if assistant is not None:
                result['assistant'] = {
                    "name": assistant.name,
                    "role": assistant.role,
                    "phone": assistant.phone,
                    "img_url": f"/user/{assistant.id}/img"
                }

        return jsonify(result)


    @app.route("/machine/<id>/resolve", methods=['GET'])
    def resolve_danger(id):
        sim.resolve_danger_mode(id)
        return jsonify({"message": "Danger resolved", "result": True})


    @app.route("/machine/<id>/data", methods=['GET'])
    def get_machine_data(id):
        data = MachineData.query.filter(MachineData.machine_id==id)\
            .order_by(MachineData.timestamp.desc()).limit(10).all()

        result = []

        for d in data:
            result.append({
                "machine_id": d.machine_id,
                "values": [d.value1, d.value2, d.value3],
                "timestamp": d.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify(result)


    @app.route("/machine/<id>/data/update", methods=['GET'])
    def get_update_data(id):
        values = sim.generate(id)
        return jsonify({
            "machine_id": id,
            "values": values,
            "timestamp": datetime.datetime.now().isoformat(sep=" ")
        })


    @app.route("/machine/<id>/data/last", methods=['GET'])
    def get_last_machine_data(id):
        data = MachineData.query.filter(MachineData.machine_id==id).order_by(MachineData.timestamp.desc()).first()
        if not data:
            return jsonify({"result": True})
        return jsonify({
            "machine_id": data.machine_id,
            "values": [data.value1, data.value2, data.value3],
            "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })


    @app.route("/machine/<id>/log", methods=['GET'])
    def get_machine_logs(id):
        logs = MachineLog.query.filter(MachineLog.machine_id == id).order_by(MachineLog.timestamp.desc()).all()

        result = []

        for l in logs:
            result.append({
                "user": l.user.name,
                "action": l.action,
                "timestamp": l.timestamp.strftime("%d/%m/%Y %H:%M:%S")
            })
        return jsonify(result)

    @app.route("/machine/<id>/command/<command>", methods=['POST'])
    def command_machine(id, command):
        machine = Machine.query.get(id)

        if not machine:
            raise Exception("macchina non esistente")
        
        if command == MACHINE_START:
            machine.started = True
        if command == MACHINE_RESUME:
            command = MACHINE_START
        if command == 'resolve':
            sim.resolve_danger_mode(id)
            return jsonify({"result": True})

        machine_log = MachineLog(machine_id = id, action=command, user_id=1, timestamp=datetime.datetime.now())
        db_session.add(machine_log)
        machine.status = command

        db_session.commit()

        return jsonify({"message": "Command sent", "result": True})


    @app.route("/machine/<id>/start", methods=["POST"])
    def start_machine(id):
        machine = Machine.query.filter(Machine.id==id).first()

        if not machine:
            raise Exception

        machine.started = True
        machine.status = MACHINE_START

        db_session.commit()

        return jsonify(True)


    @app.route("/machine/<id>/stop", methods=["POST"])
    def stop_machine(id):
        machine = Machine.query.filter(Machine.id==id).first()

        machine.started = False
        machine.status = MACHINE_STOP

        db_session.commit()
        
        return jsonify({"message": "Machine stopped", "result": True})


    return app

app = create_app()