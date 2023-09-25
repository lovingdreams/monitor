import requests
from common.configs.config import config as cfg
import logging


def makeContactInfoAPICall(contact_id, department, token):
    try:
        base_url = cfg.get("http", "CONTACT_INFO")
        url = f"{base_url}contact_id={contact_id}&department={department}"
        headers = {"Authorization": token}
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            return None
        json_response = resp.json()
        return {
            "id": json_response["data"]["id"],
            "department": json_response["data"]["department"],
            "organisation": json_response["data"]["organisation"],
            "first_name": json_response["data"]["first_name"],
            "last_name": json_response["data"]["last_name"],
            "email": json_response["data"]["email"],
            "phone_number": json_response["data"]["phone_number"],
            "title": json_response["data"]["title"],
            "owner": json_response["data"]["owner"],
            "designation": json_response["data"]["designation"],
            "tags": json_response["data"]["tags"],
            "company": json_response["data"]["company"],
        }
    except Exception as err:
        logging.error(f"makeContactInfoAPICall Exception: {err}", exc_info=True)
        return None
