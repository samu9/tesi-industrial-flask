from app import create_app
from app.database import init_db

if __name__== "__main__":
    init_db()
    app = create_app()
    app.run(debug=True, host='0.0.0.0')