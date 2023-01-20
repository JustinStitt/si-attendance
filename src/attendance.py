import requests
from utils import findCsrfInRawHTML, generateRandomSid
import re
import json
import os
from dotenv import load_dotenv

load_dotenv()

"""
Attendance class will carry out all the operations required to log student
attendance.
"""


class Attendance:
    def __init__(self):
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "https://fullerton.campus.eab.com/tutor_kiosk/sessions/new?location_id=6610&term=2233",
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
        course_response = self._selectCourse(content, course)
        return course_response

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
        # TODO:justinstitt some sort of fuzzy matching for courses?
        try:
            selection_idx = course_options.index(course_selection)
        except:
            error_message = {"errmessage": "You are not enrolled in this course"}
            return error_message

        # get ssi and course_id immediately following correct selection
        start = course_matches[selection_idx].start()
        _magic_threshold = 256
        ssi = self._getStudentServiceID(content[start : start + 256])
        course_id = self._getCourseID(content[start : start + 256])
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
        return response.cookies["_campus_session"]

    def _mintCampusSessionID(self, to_mint, auth_token):
        _url = "https://fullerton.campus.eab.com:443/tutor_kiosk/sessions?location_id=6610&student_service_id=18762&term=2233"
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
            "Referer": "https://fullerton.campus.eab.com/tutor_kiosk/sessions/new?location_id=6610&term=2233",
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
