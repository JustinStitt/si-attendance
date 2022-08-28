from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from attendance import Attendance
from flask_cors import CORS
import logging

logging.basicConfig(filename="record.log", level=logging.DEBUG)
app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)


class HelloWorld(Resource):
    def get(self):
        return {"Hello": "World"}


class SignIn(Resource):
    def get(self):
        args = request.args
        app.logger.info(f"/signin : {args}")
        response = jsonify({"message": "request made"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        if not len(args):
            return response
        bot = Attendance()
        bot.signIn(cwid=args["cwid"], course=args["course"])
        return response


api.add_resource(SignIn, "/signin")
api.add_resource(HelloWorld, "/")
