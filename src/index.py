from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from attendance import Attendance
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)


class HelloWorld(Resource):
    def get(self):
        return {"Hello": "World2"}


class GetCourses(Resource):
    def get(self):
        args = request.args
        bot = Attendance()
        return bot.GetCourses(args["cwid"])


class SignIn(Resource):
    def get(self):
        args = request.args
        app.logger.info(f"/signin : {args}")
        response = {"message": "request made", "errmessage": ""}
        # response.headers.add("Access-Control-Allow-Origin", "*")
        if not len(args):
            response["errmessage"] = "Did not provide CWID or Course"
            return jsonify(response)
        bot = Attendance()
        try:
            (bot_response, student_name) = bot.signIn(
                cwid=args["cwid"], course=args["course"]
            )
        except:
            response["errmessage"] = "Could not find that CWID."
            return response, 404
        if type(bot_response) == dict:
            response["errmessage"] = bot_response["errmessage"]
        status = "200" if not len(response["errmessage"]) else "400"
        response = jsonify(response)
        response.status = status
        print(f"{response.status=}")
        if status == "200":
            bot.logToSheet([args["course"], args["cwid"], student_name])
        return response


"""
Special route for logging students with No CWID to a Google Sheet. They will not
be signed into TitanNet
"""


class LogNonCWIDToSheet(Resource):
    def get(self):
        args = request.args
        app.logger.info(f"/noncwidsignin : {args}")
        bot = Attendance()
        bot.logToSheet([args["course"], args["nonCWIDStatus"], args["name"]])


api.add_resource(SignIn, "/signin")
api.add_resource(HelloWorld, "/")
api.add_resource(GetCourses, "/getcourses")
api.add_resource(LogNonCWIDToSheet, "/noncwidsignin")
