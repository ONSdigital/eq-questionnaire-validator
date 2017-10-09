from flask import Flask

from app.views.status import status_blueprint
from app.views.validate import validate_blueprint

application = Flask(__name__)
application.register_blueprint(validate_blueprint)
application.register_blueprint(status_blueprint)

if __name__ == '__main__':
    application.run()
