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


import couchdb
from cryptography.hazmat.primitives import serialization
# --------------------
# Configuration CouchDB
# --------------------
SESSIONS_DB_NAME = ""  # Name of the CouchDB database for storing student sessions
COUCHDB_URL = "" # URL of the CouchDB server
couch = couchdb.Server(COUCHDB_URL)
if SESSIONS_DB_NAME not in couch:
    sessions_db = couch.create(SESSIONS_DB_NAME)
else:
    sessions_db = couch[SESSIONS_DB_NAME]

# --------------------
# Configuration Orthanc
# --------------------
ORTHANC_URL = "" # URL of the Orthanc server
ORTHANC_NAME = "" # Username for Orthanc authentication
ORTHANC_PASSWORD = "" # Password for Orthanc authentication
ORTHANC_AUTH = (ORTHANC_NAME, ORTHANC_PASSWORD)

# --------------------
# Configuration LTI
# --------------------
# URL of the issuer (ISS) expected in the OIDC Token ID.
# This is the root URL of your LMS (Moodle).
# Must correspond exactly to the "iss" field in the LTI 1.3 token.
PLATFORM_ID = ""

# OIDC entry point for launching LTI flow 1.3.
# The user is redirected here to authenticate and obtain a token id.
MOODLE_AUTH_URL = ""

# Endpoint to retrieve Moodle's JWT public key.
# Used to verify the RS256 signature of id_tokens.
MOODLE_CERT_URL = ""

# URL to exchange the client_assertion (JWT) for an OAuth2 access_token,
# necessary for the NRPS (Names and Roles) service, for example.
MOODLE_TOKEN_URL = ""

# Unique identifier for your tool (Client ID) registered in Moodle.
# Must correspond to the "aud" (audience) of the token and be authorised by your LMS.
CLIENT_ID = ""
AFFICHAGE_MOODLE = "Viewer" #choice between "OrthanFlow" or "Viewer" for the display of the tool in Moodle for students 

KID = "" # Key ID used to identify the public key in the JWKS (JSON Web Key Set).
def load_private_key(): # Load the private key from a PEM file
    with open("", "rb") as key_file:
        return serialization.load_pem_private_key(key_file.read(), password=None)

def load_public_key(): # Load the public key from a PEM file
    with open("", "rb") as key_file:
        return serialization.load_pem_public_key(key_file.read())

PRIVATE_KEY = load_private_key()
PUBLIC_KEY = load_public_key()

