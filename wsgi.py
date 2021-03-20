import logging

from industrial import app


if __name__ == "__main__":
    logging.basicConfig(name=__name__, filename="WSGI.log", format='%(asctime)s - %(message)s', level=logging.INFO)
    app.run()