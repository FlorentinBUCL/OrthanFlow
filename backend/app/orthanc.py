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


import requests
from flask import jsonify
from app.config import ORTHANC_URL, ORTHANC_AUTH, sessions_db

def get_studies_logic():
    """
    Retrieves all available DICOM studies from the Orthanc server.

    For each study:
    - Checks if it contains Whole Slide Imaging (WSI) data (based on modality 'SM').
    - Adds study and series metadata for frontend display.
    - Generates appropriate viewer links based on study type (WSI or classic).

    Returns:
        JSON: Dictionary with key "Studies" containing a list of studies.
    """
    try:
        response = requests.get(f"{ORTHANC_URL}/studies", auth=ORTHANC_AUTH,
                                params={"expand": "true", "includeField": "All"})
        response.raise_for_status()
        studies_data = response.json()
        studies_to_front = []

        for study in studies_data:
            is_wsi = False
            for serie in study.get('Series', []):
                serie_response = requests.get(f"{ORTHANC_URL}/series/{serie}", auth=ORTHANC_AUTH)
                serie_response.raise_for_status()
                serie_data = serie_response.json()
                if serie_data.get('MainDicomTags', {}).get('Modality') == 'SM':
                    is_wsi = True
                    break
            studies_to_front.append({
                "is_study": True,
                "_id": study.get('ID', 'N/A'),
                "date": study.get('MainDicomTags', {}).get('StudyDate', 'N/A'),
                "institutionName": study.get('MainDicomTags', {}).get('InstitutionName', 'N/A'),
                "referringPhysicianName": study.get('MainDicomTags', {}).get('ReferringPhysicianName', 'N/A'),
                "requestedProcedureDescription": study.get('MainDicomTags', {}).get('RequestedProcedureDescription', 'N/A'),
                "description": study.get('MainDicomTags', {}).get('StudyDescription', 'N/A'),
                "studyUID": study.get('MainDicomTags', {}).get('StudyInstanceUID', 'N/A'),
                "PatientName": study.get('PatientMainDicomTags', {}).get('PatientName', 'N/A'),
                "series": study.get('Series', []),
                "is_wsi": is_wsi,
                "links": generate_study_link(
                    study.get('ID', 'N/A'),
                    study.get('MainDicomTags', {}).get('StudyInstanceUID', 'N/A'),
                    is_wsi
                )
            })
        return jsonify({"Studies": studies_to_front})
    except requests.exceptions.RequestException as e:
        return jsonify({"Error": str(e)}), 500


def get_series_logic(study_id, study_uid=None, is_wsi=False):
    """
    Retrieves series for a given DICOM study.

    Args:
        study_id (str): Internal Orthanc ID of the study.
        study_uid (str, optional): DICOM UID of the study.
        is_wsi (bool): Indicates whether the study is Whole Slide Imaging.

    Returns:
        JSON: Dictionary with key "Series" containing a list of series.
    """
    try:
        response = requests.get(f"{ORTHANC_URL}/studies/{study_id}/series", auth=ORTHANC_AUTH,
                                params={"expand": "true", "includeField": "All"})
        response.raise_for_status()
        series_data = response.json()
        series_list = []
        for serie in series_data:
            series_list.append({
                "is_study": False,
                "serieID": serie.get('ID', 'N/A'),
                "modality": serie.get('MainDicomTags', {}).get('Modality', 'N/A'),
                "bodyPart": serie.get('MainDicomTags', {}).get('BodyPartExamined', 'N/A'),
                "operator": serie.get('MainDicomTags', {}).get('OperatorsName', 'N/A'),
                "protocol": serie.get('MainDicomTags', {}).get('ProtocolName', 'N/A'),
                "descriptionProcedure": serie.get('MainDicomTags', {}).get('PerformedProcedureStepDescription', 'N/A'),
                "description": serie.get('MainDicomTags', {}).get('SeriesDescription', 'N/A'),
                "seriesUID": serie.get('MainDicomTags', {}).get('SeriesInstanceUID', 'N/A'),
                "links": generate_series_link(study_uid, serie.get('ID', 'N/A'),
                                               serie.get('MainDicomTags', {}).get('SeriesInstanceUID', 'N/A'),
                                               is_wsi)
            })
        return jsonify({"Series": series_list})
    except requests.exceptions.RequestException as e:
        return jsonify({"Error": str(e)}), 500

def search_studies_logic(term, study_type):
    """
    Searches for studies based on a keyword and optional type filter.

    Args:
        term (str): Search term (required).
        study_type (str): Optional type filter ("classic" or "wsi").

    Returns:
        JSON: Dictionary with key "Studies" containing matching studies.
    """
    if not term:
        return jsonify({"Error": "A search term is required"}), 400
    try:
        response = requests.get(f"{ORTHANC_URL}/studies", auth=ORTHANC_AUTH,
                                params={"expand": "true", "includeField": "All"})
        response.raise_for_status()
        studies_data = response.json()
        results = []

        for study in studies_data:
           
            is_wsi = False
            for serie_id in study.get('Series', []):
                serie_response = requests.get(f"{ORTHANC_URL}/series/{serie_id}", auth=ORTHANC_AUTH)
                serie_response.raise_for_status()
                serie_data = serie_response.json()
                if serie_data.get('MainDicomTags', {}).get('Modality') == 'SM':
                    is_wsi = True
                    break

            study_info = {
                "_id": study.get('ID', 'N/A'),
                "date": study.get('MainDicomTags', {}).get('StudyDate', 'N/A'),
                "institutionName": study.get('MainDicomTags', {}).get('InstitutionName', 'N/A'),
                "referringPhysicianName": study.get('MainDicomTags', {}).get('ReferringPhysicianName', 'N/A'),
                "requestedProcedureDescription": study.get('MainDicomTags', {}).get('RequestedProcedureDescription', 'N/A'),
                "description": study.get('MainDicomTags', {}).get('StudyDescription', 'N/A'),
                "studyUID": study.get('MainDicomTags', {}).get('StudyInstanceUID', 'N/A'),
                "PatientName": study.get('PatientMainDicomTags', {}).get('PatientName', 'N/A'),
                "series": study.get('Series', []),
                "is_wsi": is_wsi,
                "links": generate_study_link(study.get('ID', 'N/A'),
                                             study.get('MainDicomTags', {}).get('StudyInstanceUID', 'N/A'),
                                             is_wsi)
            }

            if any(term.lower() in str(value).lower() for value in study_info.values() if isinstance(value, str)):
                if study_type == "classic" and is_wsi:
                    continue
                if study_type == "wsi" and not is_wsi:
                    continue
                results.append(study_info)

        return jsonify({"Studies": results})
    except requests.exceptions.RequestException as e:
        return jsonify({"Error": str(e)}), 500
    
def generate_study_link(study_id, study_uid, is_wsi):
    """
    Generates viewer URLs for a given study.

    Args:
        study_id (str): Internal Orthanc ID.
        study_uid (str): DICOM UID.
        is_wsi (bool): Whether the study is WSI.

    Returns:
        list: Viewer link dictionaries.
    """
    links = []
    if is_wsi:
        links.extend([
        {
            'label': 'Stone',
            'url': f"{ORTHANC_URL}/stone-webviewer/index.html?study={study_uid}"
        },
        {
            'label': 'VolView',
            'url': f"{ORTHANC_URL}/volview/index.html?names=[archive.zip]&urls=[../studies/{study_id}/archive]"
        }])
    else:
        links.extend([
            {
                'label': 'Stone',
                'url': f"{ORTHANC_URL}/stone-webviewer/index.html?study={study_uid}"
            },
            {
                'label': 'OHIF',
                'url': f"{ORTHANC_URL}/ohif/viewer?url=../studies/{study_id}/ohif-dicom-json"
            },
            {
                'label': 'OHIF VR',
                'url': f"{ORTHANC_URL}/ohif/viewer?hangingprotocolId=mprAnd3DVolumeViewport&url=../studies/{study_id}/ohif-dicom-json"
            },
            {
                'label': 'VolView',
                'url': f"{ORTHANC_URL}/volview/index.html?names=[archive.zip]&urls=[../studies/{study_id}/archive]"
            }
        ])
    return links

def generate_series_link(study_uid, serie_id, series_uid, is_wsi):
    """
    Generates viewer URLs for a given series.

    Args:
        study_uid (str): DICOM Study UID.
        serie_id (str): Internal Orthanc ID.
        series_uid (str): DICOM Series UID.
        is_wsi (bool): Whether the series is WSI.

    Returns:
        list: Viewer link dictionaries.
    """
    links = []
    if is_wsi:
        links.extend([
            {
                'label': 'VolView',
                'url': f"{ORTHANC_URL}/volview/index.html?names=[archive.zip]&urls=[../series/{serie_id}/archive]"
            },
            {
                'label': 'WholeSlide',
                'url': f"{ORTHANC_URL}/wsi/app/viewer.html?series={serie_id}"
            }
        ])
    else:
        links.extend([
            {
                'label': 'Stone',
                'url': f"{ORTHANC_URL}/stone-webviewer/index.html?study={study_uid}&series={series_uid}"
            },
            {
                'label': 'VolView',
                'url': f"{ORTHANC_URL}/volview/index.html?names=[archive.zip]&urls=[../series/{serie_id}/archive]"
            }
        ])
    return links

def save_session_logic(data):
    """
    Saves a session's viewer URL for quick access.

    Args:
        data (dict): Contains "session" and "viewer_url" keys.

    Returns:
        JSON: Confirmation message or error.
    """
    session_id = data.get("session")
    viewer_url = data.get("viewer_url")
    if not session_id or not viewer_url:
        return jsonify({"Error": "Missing session_id or viewer_url"}), 400
    sessions_db[session_id] = {"session": session_id, "viewer_url": viewer_url}
    return jsonify({"Message": "Session successfully recorded", "session": session_id})
