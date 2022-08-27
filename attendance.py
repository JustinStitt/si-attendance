import requests
from utils import findCsrfInRawHTML
import re

"""
Attendance class will carry out all the operations required to log student
attendance.
"""


class Attendance:
    def __init__(self):
        self._cookies = {
            "apt.uid": "AP-ANT1MXI6D1QH-2-1661582339717-13974216.0.2.f37f524a-a8fe-4d8f-b456-c247ba8e82d3",
            "_campus_session": "6093f5b26c2deb962a40434ae70e56f0",
            "apt.sid": "AP-ANT1MXI6D1QH-2-1661582339717-93577811",
        }
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "https://fullerton.campus.eab.com/tutor_kiosk/sessions/new?location_id=6610&term=2227",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Te": "trailers",
        }

    def _getAuthToken(self):
        _url = "https://fullerton.campus.eab.com:443/tutor_kiosk/student_session/new"
        response = requests.get(_url, headers=self._headers, cookies=self._cookies)
        raw = response.content
        return findCsrfInRawHTML(raw)

    def signIn(self, cwid: str, course: str):
        response = self._enterCWID(cwid)
        if response.status_code != 200:
            raise ValueError(
                f"Not OK response code: Got: {response.status_code} | Expected: 200"
            )
        content = str(response.content)
        course_response = self._selectCourse(content, course)
        # print(course_response.status_code)
        # print(course_response.content)
        return course_response.status_code

    def _enterCWID(self, cwid: str):
        auth_token = self._getAuthToken()
        _url = "https://fullerton.campus.eab.com:443/tutor_kiosk/student_session"
        _data = {
            "utf8": "\xe2\x9c\x93",
            "authenticity_token": auth_token,
            "student_id": cwid,
        }
        response = requests.post(
            _url, headers=self._headers, cookies=self._cookies, data=_data
        )
        return response

    def _selectCourse(self, content, course_selection):
        needle = "(?<=Click here to choose\W).*?(?= )"
        course_matches = [m for m in re.finditer(needle, content)]
        course_options = [content[m.start() : m.end()].strip() for m in course_matches]
        # TODO:justinstitt some sort of fuzzy matching for courses?
        try:
            selection_idx = course_options.index(course_selection)
        except:
            raise IndexError(
                f"Course Selection: {course_selection} not found in course list: {course_options}"
            )
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
        needle = "(?<=course_id=)\d+"
        result = re.search(needle, content).group()
        return result

    def _getStudentServiceID(self, content):
        needle = "(?<=student_service_id=)\d+"
        result = re.search(needle, content).group()
        return result
