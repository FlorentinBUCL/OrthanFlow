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


import json
import uuid
import urllib.parse
import requests
import jwt
import time
from jwt.algorithms import RSAAlgorithm
from flask import jsonify, session, redirect, make_response

from app.config import (
    PLATFORM_ID,
    CLIENT_ID,
    MOODLE_AUTH_URL,
    MOODLE_CERT_URL,
    MOODLE_TOKEN_URL,
    KID,
    PRIVATE_KEY,
    PUBLIC_KEY,
    sessions_db,
    AFFICHAGE_MOODLE
)

def get_moodle_pubkey(kid):
    """
    Retrieves the public key associated with a key ID (kid) from Moodle.

    Args:
        kid (str): The key identifier.

    Returns:
        rsa.RSAPublicKey: The RSA public key.

    Raises:
        ValueError: If no key matches the kid provided.
    """
    response = requests.get(MOODLE_CERT_URL).json()
    for k in response['keys']:
        if k['kid'] == kid:
            return RSAAlgorithm.from_jwk(json.dumps(k))
    raise ValueError( "Moodle public key not found" )


def get_token(id_token):
    """
    Decodes and verifies a JWT token received from Moodle.

    Args:
        id_token (str): The JWT identity token.

    Returns:
        dict: The decoded contents of the token.

    Raises:
        ValueError: In the event of a validation problem (nonce, exp, client_id, etc.).
    """
    try :
        header = jwt.get_unverified_header(id_token)
        kid = header.get('kid')
        moodle_pubkey = get_moodle_pubkey(kid)
        token = jwt.decode(id_token, moodle_pubkey, algorithms=['RS256'], audience=CLIENT_ID)
        
        if token.get("iss") != PLATFORM_ID:
            raise ValueError("ISS invalid")
        cli_id = token.get("aud")
        if isinstance(cli_id, list):
            if CLIENT_ID not in cli_id:
                raise ValueError("CLIENT ID invalid")
            if len(cli_id) > 1 and not token.get("azp"):
                raise ValueError("azp missing for multiple audiences")
            if token.get("azp") and token.get("azp") != CLIENT_ID:
                raise ValueError("azp invalid")
        if cli_id != CLIENT_ID:
            raise ValueError("CLIENT ID invalid")
        sub = token.get("sub")
        if sub is None or sub == "":
            raise ValueError("SUB missing")
        if len(sub) > 255:
            raise ValueError("SUB length greater than 255 characters")
        if not sub.isascii():
            raise ValueError("SUB contains non-ASCII characters")
        if token.get("nonce") != session.get('nonce'):
            raise ValueError("NONCE invalid")
        now = int(time.time())
        if token.get("exp") < now:
            raise ValueError("Token expired")
        if token.get("iat") > now:
            raise ValueError("Token sent too late")
        return token
    except jwt.InvalidSignatureError:
        raise ValueError("Invalid token signature")

def get_nrps_access():
    """
    Gets an OAuth 2.0 access token to query Moodle's NRPS endpoint.

    Returns:
        str: The NRPS access token.

    Raises:
        ValueError: On authentication failure.
    """

    assertion_payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": MOODLE_TOKEN_URL,
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
        "jti": str(uuid.uuid4()),
    }
    headers = {"kid": KID}  
    client_assertion = jwt.encode(assertion_payload, PRIVATE_KEY, algorithm="RS256", headers=headers)

    data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": client_assertion,
        "scope": "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
    }

    response = requests.post(MOODLE_TOKEN_URL, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise ValueError("Error recovering NRPS acces token")


def get_member_nrps(nrps_url):
    """
    Retrieves the list of members of a context via NRPS.

    Args:
        nrps_url (str): The URL of the NRPS endpoint.

    Returns:
        list: A list of registered users (dict).

    Raises:
        ValueError: If the API call fails.
    """
    access_token = get_nrps_access()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
    }
    response = requests.get(nrps_url, headers=headers)
    if response.status_code == 200:
        return response.json().get("members", [])
    else:
        raise ValueError("Error when retrieving NRPS members")

def enrolled(nrps_url, sub, authorized_roles):
    """
    Checks if a user is registered and active via NRPS.

    Args:
        nrps_url (str): THE NRPS URL.
        sub (str): The identifier of the user to be checked.
        authorized_roles (list): List of roles that authorize access.

    Returns:
        bool: True if the student is enrolled, False otherwise.
    """
    try:
        members = get_member_nrps(nrps_url)
        authorized = False
        for m in members:
            if (m.get("user_id") == sub and m.get("status") == "Active" and
                any(role in m.get("roles", []) for role in authorized_roles)):
                authorized = True
                return authorized
                
    except Exception as e:
        return (f"Error verifying user registration : {str(e)}")


def jwks_logic():
    """
    Provides the public key in JWK format for discovery requests.

    Returns:
        flask.Response: JSON response containing the public key.
    """
    jwk = {
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "kid": "2",
        "n": PUBLIC_KEY,
        "e": "AQAB",
    }
    return jsonify({"keys": [jwk]}), 200


def oidc_logic(request):
    """
    Starts the OIDC flow by generating the parameters needed to redirect to Moodle.

    Args:
        request (flask.Request): Incoming HTTP request.

    Returns:
        flask.Response: Redirects to the Moodle authentication URL.
    """
    session['state'] = str(uuid.uuid4())
    session['nonce'] = str(uuid.uuid4())
    
    if request.method == "POST":
        data = request.form
    else :
        data = request.args
    
    if not data.get('iss') or data.get('iss') != PLATFORM_ID:
        return jsonify({"Error": "ISS missing or incorrect"}), 400
    if not data.get('target_link_uri'):
        return jsonify({"Error": "target_link_uri missing"}), 400
    if not data.get('login_hint'):
        return jsonify({"Error": "login_hint missing"}), 400
    
    parameters = {
        "response_type": "id_token",
        "scope": "openid",
        "login_hint": data.get('login_hint'),
        "lti_message_hint": data.get('lti_message_hint'),
        "state": session['state'],
        "redirect_uri": data.get('target_link_uri'),
        "client_id": CLIENT_ID,
        "nonce": session['nonce'],
        "response_mode": "form_post",
        "lti_deployment_id": data.get('lti_deployment_id'),
        "prompt": "none",
    }
    return redirect(f"{MOODLE_AUTH_URL}?{urllib.parse.urlencode(parameters)}"), 302


def nrps_logic(request):
    """
    Retrieves the list of members of a context via an LTI token.

    Args:
        request (flask.Request): HTTP request containing the `id_token`.

    Returns:
        flask.Response: JSON containing the members or an error.
    """
    state = request.args.get('state')
    if state != session.get('state'):
        return jsonify({"Error": "State invalid"}), 400
    id_token = request.args.get('id_token')
    payload = get_token(id_token)
    nrps_url = payload.get("https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice", {}).get("context_memberships_url")
    if not nrps_url:
        return jsonify({"Error": "NRPS URL not found"}), 400
    members = get_member_nrps(nrps_url)
    return jsonify({"Members": members}), 200

def dl_request_logic(request):
    """
    Handles Deep Linking requests (content selection from Moodle).

    Args:
        request (flask.Request): HTTP POST request with `id_token`.

    Returns:
        flask.Response: Redirect to the frontend if the user is authorised.
    """
    state = request.form.get('state')
    if state != session.get('state'):
        return jsonify({"Error": "State invalid"}), 400
    id_token = request.form.get('id_token')

    try:
        payload = get_token(id_token)

        message_type = payload.get("https://purl.imsglobal.org/spec/lti/claim/message_type")
        sub = payload.get("sub")
        if message_type != "LtiDeepLinkingRequest":
            return jsonify({"Error": "LTI message type not supported for Deep Linking"}), 400

        nrps_claim = payload.get("https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice", {})
        nrps_url = nrps_claim.get("context_memberships_url")
        authorized_roles = [
                    "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
                    "http://purl.imsglobal.org/vocab/lis/v2/membership#Administrator", 
                    "Instructor",
                    "Administrator"
                ]

        authorized = enrolled(nrps_url, sub, authorized_roles)
        if authorized:
            session['dl_aud'] = payload.get("iss")
            deep_link_settings = payload.get("https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings", {})
            session['dl_urlret'] = deep_link_settings.get("deep_link_return_url")
            session['dl_deployment_id'] = payload.get("https://purl.imsglobal.org/spec/lti/claim/deployment_id")
            session['dl_title'] = payload.get("https://purl.imsglobal.org/spec/lti/claim/resource_link", {}).get("title")
            session['dl_data'] = deep_link_settings.get("data")
            session['dl_nonce'] = payload.get("nonce")
            return redirect("http://localhost:5173/"), 302
        
        else:
            
            return jsonify({"Error": "Access denied: only instructors or administrators can access the selection interface"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def dl_submit_logic(request):
    """
    Sends the Deep Linking response to Moodle with the selected item.

    Args:
        request (flask.Request): HTTP POST request containing the selected information.

    Returns:
        tuple: HTML redirect, HTTP code and headers.
    """
    data = request.form
    session_id = data.get('session_id')
    title = data.get('title')
    content_items = {
        "type": "ltiResourceLink",
        "url": "http://localhost:5000/launch",
        "title": title,
        "custom": {
            "res_id": session_id
        },
    }
    dl_response = {
        "iss": CLIENT_ID,
        "aud": session.get('dl_aud'),
        "exp": int(time.time()) + 600,
        "iat": int(time.time()),
        "nonce": session.get('dl_nonce'),
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": session.get('dl_deployment_id'),
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [content_items],
        "https://purl.imsglobal.org/spec/lti-dl/claim/data": session.get('dl_data', "")
    }
    headers = {"kid": KID}
    resp_jwt = jwt.encode(dl_response, PRIVATE_KEY, algorithm="RS256", headers=headers)
    deep_link_return_url = session.get('dl_urlret')
    if not deep_link_return_url:
        raise ValueError("Deep Linking return URL not found")
    html = (
        f'<form id="dl_response" action="{deep_link_return_url}" method="POST">'
        f'<input type="hidden" name="JWT" value="{resp_jwt}"/></form>'
        f"<script type=\"text/javascript\">document.getElementById('dl_response').submit();</script>"
    )
    return html, 200, {'Content-Type': 'text/html'}


def launch_logic(request):
    """
    Handles the LTI launch of type `LtiResourceLinkRequest` or `LtiDeepLinkingRequest`.

    Args:
        request (flask.Request): HTTP POST request containing the `id_token`.

    Returns:
        flask.Response: Error redirection or JSON depending on role and message type.
    """
    state = request.form.get('state')
    if state != session.get('state'):
        return jsonify({"Error": "State invalid"}), 400

    id_token = request.form.get('id_token')
    try:
        payload = get_token(id_token)
        message_type = payload.get("https://purl.imsglobal.org/spec/lti/claim/message_type")
        if message_type == "LtiResourceLinkRequest":
            nrps_claim = payload.get("https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice", {})
            nrps_url = nrps_claim.get("context_memberships_url")
            sub = payload.get("sub")
            authorized_roles = [
                    "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
                    "http://purl.imsglobal.org/vocab/lis/v2/membership#Administrator",
                    "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
                    "Learner", 
                    "Instructor",
                    "Administrator"
                ]

            custom_claim = payload.get("https://purl.imsglobal.org/spec/lti/claim/custom", {})
            res_id = custom_claim.get("res_id")
            if not res_id:
                raise ValueError("No res_id in the token")

            viewer_url = sessions_db.get(res_id, {}).get('viewer_url')
            if not viewer_url:
                raise ValueError(f"No session found for res_id {res_id}")

            resource_link_claim = payload.get("https://purl.imsglobal.org/spec/lti/claim/resource_link", {})
            description = resource_link_claim.get("description", "")

            authorized = enrolled(nrps_url, sub, authorized_roles)
            if authorized:
                
                
                if AFFICHAGE_MOODLE == "OrthanFlow":
                    token_payload = {
                        "res_id": res_id,
                        "viewer_url": viewer_url,
                        "description": description,
                        "exp": int(time.time()) + 600
                    }
                    token = jwt.encode(token_payload, PRIVATE_KEY, algorithm="RS256")
                    redirect_url = f"http://localhost:5173/student?token={token}"
                elif( AFFICHAGE_MOODLE == "Viewer"):
                    redirect_url = f"{viewer_url}"
                else:
                    raise ValueError("AFFICHAGE_MOODLE must be 'OrthanFlow' or 'Viewer'")
                return redirect(redirect_url), 302

            else:
                return jsonify({"Error": "Access denied"}), 403
        else:
            return jsonify({"Error": f"LTI message not supported : {message_type}"}), 400

    except jwt.ExpiredSignatureError:
        return jsonify({"Error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"Error": "Token invalid"}), 401
    except Exception as e:
        print(f"Error in /launch : {e}")
        raise


def validate_token_logic(request):
    """
    Validates a token generated for the student (JWT signed on the backend side).

    Args:
        request (flask.Request): POST request containing the token.

    Returns:
        flask.Response: Information contained in the token if valid.
    """
    data = request.get_json()
    token = data.get("token")
    if not token:
        return jsonify({"Error": "Token missing"}), 400

    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return jsonify({
            "res_id": payload.get("res_id"),
            "viewer_url": payload.get("viewer_url"),
            "description": payload.get("description")
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({"Error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"Error": "Token invalid"}), 401

