from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from attendance import Attendance
from flask_cors import CORS
import logging

# logging.basicConfig(filename="record.log", level=logging.DEBUG)
app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)


class HelloWorld(Resource):
    def get(self):
        return {"Hello": "World"}


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
        bot_response = bot.signIn(cwid=args["cwid"], course=args["course"])
        if type(bot_response) == dict:
            response["errmessage"] = bot_response["errmessage"]
        status = "200" if not len(response["errmessage"]) else 400
        response = jsonify(response)
        response.status = status
        return response


api.add_resource(SignIn, "/signin")
api.add_resource(HelloWorld, "/")
api.add_resource(GetCourses, "/getcourses")
