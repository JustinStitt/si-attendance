from flask import Flask, request
from flask_restful import Resource, Api
from attendance import Attendance

app = Flask(__name__)
api = Api(app)


class HelloWorld(Resource):
    def get(self):
        return {"Hello": "World"}


class SignIn(Resource):
    def post(self):
        args = request.args
        print(args)
        bot = Attendance()
        response = bot.signIn(cwid=args["cwid"], course=args["course"])
        return {"course_selection_status_code": response}


api.add_resource(SignIn, "/signin")
api.add_resource(HelloWorld, "/")
