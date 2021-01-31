from flask import Flask, jsonify

from app.database import db_session, Area, Sector, Machine, MachineData
from app.constants import MACHINE_RUN, MACHINE_STOP, MACHINE_PAUSE

def create_app():
    app = Flask(__name__)
    # app.config.from_envvar("AREA")
    app.config.from_mapping(
        AREA=1,
        SQLALCHEMY_DATABASE_URI="mysql+mysqldb://root:@localhost[:3306]/industrial"
        )
    


    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

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
                "status": m.status
            })
        return jsonify(result)


    @app.route("/machine/<id>/start", methods=["POST"])
    def start_machine(id):
        machine = Machine.query.filter(Machine.id==id).first()

        if not machine:
            raise Exception

        machine.started = True
        machine.status = MACHINE_RUN

        db_session.commit()

        return jsonify(True)

    @app.route("/machine/<id>/stop", methods=["POST"])
    def stop_machine(id):
        machine = Machine.query.filter(Machine.id==id).first()

        machine.started = False
        machine.status = MACHINE_STOP

        db_session.commit()
        
        return jsonify(True)


    @app.route("/machine/<id>/data", methods=['GET'])
    def get_machine_data(id):
        data = MachineData.query.filter(MachineData.machine_id==id).order_by(MachineData.timestamp.desc()).all()

        result = []

        for d in data:
            result.append({
                "machine_id": d.machine_id,
                "values": [d.value1, d.value2, d.value3],
                "timestamp": d.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify(result)

    @app.route("/machine/<id>/data/last", methods=['GET'])
    def get_last_machine_data(id):
        data = MachineData.query.filter(MachineData.machine_id==id).order_by(MachineData.timestamp.desc()).first()
        if not data:
            return jsonify({})
        return jsonify({
            "machine_id": data.machine_id,
            "values": [data.value1, data.value2, data.value3],
            "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

    return app
