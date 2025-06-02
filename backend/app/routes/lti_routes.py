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


from flask import Blueprint, request
from app.lti import (
    jwks_logic,
    oidc_logic,
    launch_logic,
    dl_request_logic,
    dl_submit_logic,
    nrps_logic,
    validate_token_logic
)

lti = Blueprint('lti', __name__)

@lti.route("/jwks", methods=["GET"])
def jwks():
    """
    Returns the JSON Web Key Set (JWKS) required for LTI authentication.
    """
    return jwks_logic()

@lti.route("/oidc", methods=["GET", "POST"])
def oidc():
    """
    Handles the OpenID Connect (OIDC) login initiation request.
    """
    return oidc_logic(request)

@lti.route("/launch", methods=["POST"])
def launch():
    """
    Handles the LTI 1.3 launch request. This is typically triggered when a user opens the tool from the LMS.
    """
    return launch_logic(request)

@lti.route("/deep", methods=["POST"])
def dl_request():
    """
    Handles Deep Linking (DL) request for content selection and configuration.
    """
    return dl_request_logic(request)

@lti.route("/dl_submit", methods=["POST"])
def dl_submit():
    """
    Handles the submission of content from the Deep Linking workflow.
    """
    return dl_submit_logic(request)

@lti.route("/nrps", methods=["GET"])
def nrps():
    """
    Fetches information from the Names and Roles Provisioning Service (NRPS), 
    which provides a list of users enrolled in the context (e.g., a course).
    """
    return nrps_logic(request)


@lti.route("/lti/validate_token", methods=["POST"])
def validate_token():
    """
    Validates a JWT token and returns selected claims.
    """
    return validate_token_logic(request)