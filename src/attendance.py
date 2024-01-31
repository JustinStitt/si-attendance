import requests
from utils import findCsrfInRawHTML, generateRandomSid
import re
import json
import os
from dotenv import load_dotenv
import pygsheets
from datetime import datetime
import pytz
import sys

load_dotenv()
try:
    gc = pygsheets.authorize(service_file="creds.json")  # load Google API Client
    sheet = gc.open("si-attendance-log")[0]
except:
    print("Error: Failed to Connect to Google Sheet!")

"""
Attendance class will carry out all the operations required to log student
attendance.
"""


class Attendance:
    def __init__(self):
        self._term = None
        self._term_fallback = 2243
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": f"https://fullerton.campus.eab.com/tutor_kiosk/sessions/new?location_id=6610&term={self._term}",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Te": "trailers",
        }

        self._campus_session = self._getCampusSessionID()
        # self._campus_session = "4511950af6b067938fd950456f1b89bf"

        self._cookies = {
            "apt.uid": "AP-ANT1MXI6D1QH-2-1661818966007-83815959.0.2.f37f524a-a8fe-4d8f-b456-c247ba8e82d3",
            "_campus_session": f"{self._campus_session}",  # campus session needs to be changed ~5-7 days it looks like
            "apt.sid": f"AP-ANT1MXI6D1QH-2-1663180509893-{generateRandomSid()}",
        }

        self._auth_token = self._getAuthToken()
        self._mintCampusSessionID(self._campus_session, self._auth_token)

    def _getAuthToken(self):
        _url = "https://fullerton.campus.eab.com:443/tutor_kiosk/student_session/new"
        response = requests.get(_url, headers=self._headers, cookies=self._cookies)
        raw = response.content
        return findCsrfInRawHTML(raw)

    def signIn(self, cwid: str, course: str):
        response = self._enterCWID(cwid)
        if type(response) == dict:
            return response
        if response.status_code != 200:
            raise ValueError(
                f"Not OK response code: Got: {response.status_code} | Expected: 200"
            )
        content = str(response.content)
        student_name = self._extractNameFromContent(content)
        course_response = self._selectCourse(content, course)
        return (course_response, student_name)

    def _enterCWID(self, cwid: str):
        # auth_token = self._getAuthToken()
        _url = "https://fullerton.campus.eab.com:443/tutor_kiosk/student_session"
        _data = {
            "utf8": "\xe2\x9c\x93",
            "authenticity_token": self._auth_token,
            "student_id": cwid,
        }
        response = requests.post(
            _url, headers=self._headers, cookies=self._cookies, data=_data
        )
        if str(response.content).find("Student ID") != -1:
            return {"errmessage": "Invalid CWID"}
        return response

    def _extractNameFromContent(self, content):
        needle = "(?<='kiosk-user-name\\\\\\'>\\\\n)\w*"
        name = re.findall(needle, content)[0]
        return name

    def GetCourses(self, cwid: str):
        response = self._enterCWID(cwid)
        if type(response) == dict:
            return {"errmessage": "Invalid CWID"}
        content = str(response.content)
        needle = '((?<=Click here to choose: )\w*-\d+[a-zA-z]*(-\d+)*.+?(?=\(|"))'
        courses = re.findall(needle, content)
        return json.dumps(courses)

    def _selectCourse(self, content, course_selection):
        needle = "(?<=Click here to choose: ).*?\d+(?=[A-Za-z]*-)"
        course_matches = [m for m in re.finditer(needle, content)]
        course_options = [content[m.start() : m.end()].strip() for m in course_matches]
        try:
            selection_idx = course_options.index(course_selection)
        except:
            error_message = {"errmessage": "You are not enrolled in this course"}
            return error_message

        # get ssi and course_id immediately following correct selection
        start = course_matches[selection_idx].start()
        _magic_threshold = 256
        ssi = self._getStudentServiceID(content[start : start + _magic_threshold])
        course_id = self._getCourseID(content[start : start + _magic_threshold])
        # make the post request with given info
        response = requests.post(
            f"https://fullerton.campus.eab.com/tutor_kiosk/recorded_visits?course_id={course_id}&student_service_id={ssi}",
            headers=self._headers,
            cookies=self._cookies,
        )
        return response

    def _getCourseID(self, content):
        # TODO:justinstitt map courses to course ids. This will enable students
        # --to join courses they aren't enrolled in.
        needle = "(?<=course_id=)\d+"
        result = re.search(needle, content).group()
        return result

    def _getStudentServiceID(self, content):
        needle = "(?<=student_service_id=)\d+"
        result = re.search(needle, content).group()
        return result

    def _getCampusSessionID(self):
        _url = "https://fullerton.campus.eab.com:443/session.json"
        _json = {
            "login": os.environ.get("secretKioskUsername"),
            "password": os.environ.get("secretKioskPassword"),
        }
        _cookies = {
            "apt.uid": "AP-ANT1MXI6D1QH-2-1661818966007-83815959.0.2.f37f524a-a8fe-4d8f-b456-c247ba8e82d3",
            "_campus_session": "7148f5184aa59852e5998046b3dc79db",
            "apt.sid": "AP-ANT1MXI6D1QH-2-1663180509893-46247988",
        }
        response = requests.post(
            _url, headers=self._headers, json=_json, cookies=_cookies
        )

        self._setTermNumber(response.cookies["_campus_session"])

        return response.cookies["_campus_session"]

    def _setTermNumber(self, campus_session):
        _url = "https://fullerton.campus.eab.com:443/tutor_kiosk/sessions/new?time_zone=America%2FLos_Angeles"
        _cookies = {
            "apt.uid": "AP-ANT1MXI6D1QH-2-1661818966007-83815959.0.2.f37f524a-a8fe-4d8f-b456-c247ba8e82d3",
            "_campus_session": f"{campus_session}",
            "apt.sid": "AP-ANT1MXI6D1QH-2-1663180509893-46247988",
        }

        response = requests.get(_url, cookies=_cookies, headers=self._headers)

        raw = response.content
        pattern = r"(?<=term=)\d+"

        term_number = None
        try:
            term_number = int(re.findall(pattern, raw.decode("utf-8"))[0])
        except Exception as e:
            print(f"Cannot parse term number as an int: {e}")
            self._term = self._term_fallback
        else:
            self._term = term_number

    def _mintCampusSessionID(self, to_mint, auth_token):
        _url = f"https://fullerton.campus.eab.com:443/tutor_kiosk/sessions?location_id=6610&student_service_id=18762&term={self._term}"
        _headers = {
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Chromium";v="105", "Not)A;Brand";v="8"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://fullerton.campus.eab.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.5195.102 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"https://fullerton.campus.eab.com/tutor_kiosk/sessions/new?location_id=6610&term={self._term}",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
        }
        _cookies = {
            "apt.uid": "AP-ANT1MXI6D1QH-2-1661818966007-83815959.0.2.f37f524a-a8fe-4d8f-b456-c247ba8e82d3",
            "apt.sid": "AP-ANT1MXI6D1QH-2-1663184976438-87398197",
            "_campus_session": to_mint,
        }
        _data = {"_method": "post", "authenticity_token": auth_token}
        response = requests.post(_url, headers=_headers, cookies=_cookies, data=_data)
        return response.ok

    def logToSheet(self, row):
        pst_time = pytz.utc.localize(datetime.utcnow()).astimezone(
            pytz.timezone("US/Pacific")
        )
        sheet.append_table([str(pst_time), *row])
