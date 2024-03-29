import os
import random
import datetime
import logging
import uuid
import base64
from functools import wraps

from flask import Flask, jsonify, send_from_directory, request
from werkzeug.utils import secure_filename

from industrial.database import db_session, Area, Sector, Machine, MachineData, User, MachineLog, MachineImage

from industrial.constants import MACHINE_START, MACHINE_STOP, MACHINE_PAUSE, MACHINE_RESUME, RESOLVE_STEPS
from industrial.simulation import Simulation

logging.basicConfig(format='%(asctime)s %(message)s', filename='industrial.log', level=logging.INFO)

def create_app():

    log = logging.getLogger(__name__)
    app = Flask(__name__ , static_url_path='/static')

    try:
        app.config.from_envvar('INDUSTRIAL_CONFIG')
        log.info("Configurations set")
    except:
        log.error("INDUSTRIAL_CONFIG environment variable not set")
        raise Exception("INDUSTRIAL_CONFIG environment variable not set") 

    sim = Simulation(app.config['SECTOR_ID'])


    def api_response(message, result=True):
        return {
            "message": message,
            "result": result
        }

    def authenticated(f):
        @wraps(f)
        def decorated_function(**kwargs):
            auth = request.headers.get("Authorization")
            if auth != "Basic " + app.config['API_KEY']:
                log.error("Unauthorized")
                log.error(auth)
                return jsonify(api_response("Unauthorized", result=False)), 401
            return f(**kwargs)
        return decorated_function
        

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()


    @app.route('/user/<id>/img', methods=['GET'])
    def get_user_image(id):
        return send_from_directory(app.config['USER_IMG_DIR'], id + '.jpg')


    @app.route('/position', methods=['GET'])
    @authenticated
    def get_position():
        return jsonify({
            "area_id": app.config['AREA_ID'],
            "sector_id": app.config['SECTOR_ID']
        })


    @app.route('/area')
    @authenticated
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
    @authenticated
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
    @authenticated
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
    @authenticated
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
    @authenticated
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
    @authenticated
    def set_in_danger(id):
        sim.set_danger_mode(id)
        return jsonify(api_response("Danger set"))


    @app.route("/machine/<id>/danger/instruction", methods=['GET'])
    @authenticated
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
    @authenticated
    def resolve_danger(id):
        sim.resolve_danger_mode(id)
        return jsonify(api_response("Danger resolved"))


    @app.route("/machine/<id>/data", methods=['GET'])
    @authenticated
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
    @authenticated
    def get_update_data(id):
        values = sim.generate(id)
        return jsonify({
            "machine_id": id,
            "values": values,
            "timestamp": datetime.datetime.now().isoformat(sep=" ")
        })


    @app.route("/machine/<id>/data/last", methods=['GET'])
    @authenticated
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
    @authenticated
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
    @authenticated
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

        return jsonify(api_response("Command sent"))


    @app.route("/machine/<id>/start", methods=["POST"])
    @authenticated
    def start_machine(id):
        machine = Machine.query.filter(Machine.id==id).first()

        if not machine:
            raise Exception

        machine.started = True
        machine.status = MACHINE_START

        db_session.commit()

        return jsonify(True)


    @app.route("/machine/<id>/stop", methods=["POST"])
    @authenticated
    def stop_machine(id):
        machine = Machine.query.filter(Machine.id==id).first()

        machine.started = False
        machine.status = MACHINE_STOP

        db_session.commit()
        
        return jsonify(api_response("Machine stopped"))


    @app.route("/machine/<id>/image", methods=['GET'])
    def get_image_list(id):
        images = db_session.query(MachineImage.image_uuid).filter(MachineImage.machine_id==id).all()
        images_list = [i[0] for i in images]
        return jsonify(images_list)


    @app.route("/machine/<id>/image", methods=['POST'])
    @authenticated
    def post_image(id):
        image_uuid = str(uuid.uuid4())
        filename = image_uuid + "." + app.config['IMAGE_FORMAT']
        try:
            log.info("saving image")
            with open(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], filename), "wb") as f:
                image_data = base64.b64decode(request.data.decode("utf-8"))
                f.write(image_data)

        except Exception as e:
            log.exception(e)
            return jsonify(api_response("Failed to decode data", result=False))
        
        machine_image = MachineImage(image_uuid=image_uuid, machine_id=id, timestamp=datetime.datetime.now())
        db_session.add(machine_image)
        db_session.commit()

        return jsonify(api_response("Upload successful"))


    @app.route("/machine/image/<image_id>", methods=['GET'])
    @authenticated
    def serve_machine_img(image_id):
        print("ok")
        return send_from_directory(app.config['USER_IMG_DIR'] + "/uploads", image_id + '.jpg')


    return app



app = create_app()