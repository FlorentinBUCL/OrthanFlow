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
from app.orthanc import (
    get_studies_logic,
    get_series_logic,
    search_studies_logic,
    save_session_logic
)

orthanc = Blueprint('orthanc', __name__)

@orthanc.route("/studies", methods=["GET"])
def get_studies():
    """
    Returns a list of studies from Orthanc with metadata for frontend display.
    """
    return get_studies_logic()

@orthanc.route("/studies/<study_id>/series", methods=["GET"])
def get_series(study_id):
    """
    Returns a list of series for a specific study from Orthanc.
    Args:
        study_id (str): The ID of the study to retrieve series for.
    Returns:
        JSON: Dictionary with key "Series" containing a list of series for the specified study.
    """
    study_uid = request.args.get("study_uid")
    is_wsi = request.args.get("is_wsi", "false").lower() == "true"
    return get_series_logic(study_id, study_uid, is_wsi)

@orthanc.route("/search_studies", methods=["GET"])
def search_studies():
    """
    Searches for studies based on a query term and type of image.
    Args:
        query (str): The search term to filter studies.
        type (str): The type of image to filter studies (e.g., "wsi", "classic").
    Returns:
        JSON: Dictionary with key "Studies" containing a list of studies matching the search criteria.
    """
    term = request.args.get("query", "").strip().lower()
    study_type = request.args.get("type", "").lower()
    return search_studies_logic(term, study_type)

@orthanc.route("/save_session", methods=["POST"])
def save_session():
    """
    Saves a session to the database.
    """
    data = request.get_json()
    return save_session_logic(data)
