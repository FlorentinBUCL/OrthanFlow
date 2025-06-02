# This file is part of OrthanFlow.
#
# OrthanFlow is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OrthanFlow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (C) 2025 Florentin Botton


from flask import Flask
from flask_cors import CORS
from flask_session import Session

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_super_secret_key'
    
    # Configurations
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = False
    Session(app)
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)


    # Import Blueprints
    from app.routes.orthanc_routes import orthanc
    from app.routes.lti_routes import lti

    # Register Blueprints
    app.register_blueprint(orthanc)
    app.register_blueprint(lti)

    return app
