import logging

from industrial import app

logging.basicConfig(filename="app.log", format='%(asctime)s - %(message)s', level=logging.INFO)

if __name__ == "__main__":
    app.run()