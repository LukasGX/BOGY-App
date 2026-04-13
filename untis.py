from definitions import UNTIS_USERNAME, UNTIS_PASSWORD
import requests
import json
import base64

BASE_URL = "https://bogy.webuntis.com"
SCHOOL = "bogy"
USERNAME = UNTIS_USERNAME
PASSWORD = UNTIS_PASSWORD
ID = "Awesome"
def login():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
    })

    login_payload = {
        "id": ID,
        "method": "authenticate",
        "params": {
            "user": USERNAME,
            "password": PASSWORD,
            "client": ID
        },
        "jsonrpc": "2.0"
    }

    response = session.post(
        f"{BASE_URL}/WebUntis/jsonrpc.do?school={SCHOOL}",
        data=json.dumps(login_payload)
    )

    return session

def get_classes():
    session = login()

    classes_payload = {
        "id": ID,
        "method": "getKlassen",
        "params": {},
        "jsonrpc": "2.0"
    }

    classes_response = session.post(
        f"{BASE_URL}/WebUntis/jsonrpc.do?school={SCHOOL}",
        data=json.dumps(classes_payload)
    )

    return classes_response.json()

def get_users():
    session = login()

    students_payload = {
        "id": ID,
        "method": "getStudents",
        "params": {},
        "jsonrpc": "2.0"
    }

    students_response = session.post(
        f"{BASE_URL}/WebUntis/jsonrpc.do?school={SCHOOL}",
        data=json.dumps(students_payload)
    )

    teachers_payload = {
        "id": ID,
        "method": "getTeachers",
        "params": {},
        "jsonrpc": "2.0"
    }
    teachers_response = session.post(
        f"{BASE_URL}/WebUntis/jsonrpc.do?school={SCHOOL}",
        data=json.dumps(teachers_payload)
    )

    return {"teachers": teachers_response.json(), "students": students_response.json()}