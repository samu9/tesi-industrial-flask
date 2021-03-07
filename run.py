from industrial import create_industrial
from industrial.database import init_db

if __name__== "__main__":
    init_db()
    industrial = create_app()
    industrial.run(debug=True, host='0.0.0.0')