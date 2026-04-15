import json
import untis
from services.administration_service import create_class_s, create_user_s
from payloads import CreateClassRequest, CreateUserRequest

def get_untis_classes_s():
    classes = untis.get_classes()
    return classes

def import_untis_classes_s():
    classes = untis.get_classes()

    for cl in classes["result"]:
        payload = CreateClassRequest(className=cl["name"])
        create_class_s(payload)

    return {"status": "success"}

def get_untis_users_s():
    users = untis.get_users()
    return users

def import_untis_users_s():
    users = untis.get_users()
    pwT = "MusterPWLehrer"
    pwS = "MusterPW"

    for teacher in users["teachers"]["result"]:
        fore = teacher["foreName"]
        long = teacher["longName"]
        username = fore.lower().replace(' ', '') + "." + long.lower().replace(' ', '')

        payload = CreateUserRequest(
            username=username,
            firstname=fore,
            lastname=long,
            password=pwT,
            role=2,
            **{"class": None}
        )
        create_user_s(payload)

    for student in users["students"]["result"]:
        fore = student["foreName"]
        long = student["longName"]
        username = fore.lower().replace(' ', '') + "." + long.lower().replace(' ', '')

        payload = CreateUserRequest(
            username=username,
            firstname=fore,
            lastname=long,
            password=pwS,
            role=1,
            **{"class": None}
        )
        create_user_s(payload)

    return {"status": "success"}