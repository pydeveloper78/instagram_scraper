# -*- coding: utf-8 -*-

from flask import Flask, abort, jsonify, make_response
from flask_restful import Api, Resource, fields, marshal, reqparse
from instagram import contents, main


app = Flask(__name__, static_url_path="")
api = Api(app)


class InstAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'f', type=str, required=True, help='Fan Username', location='form')
        self.reqparse.add_argument(
            'b', type=str, help="Brand Username", required=True, location='form')
        super(InstAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return main(args.f, args.b), 200

    def post(self):
        args = self.reqparse.parse_args()
        return main(args.f, args.b), 200


class InstContentsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'brand', type=str, required=True, help='Brand Username', location='form')
        self.reqparse.add_argument(
            'last_post_id', type=str, help="Last Post ID", location='form')
        super(InstContentsAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        try:
            last_post_id = args.last_post_id
        except:
            last_post_id = None
        return contents(args.brand, last_post_id), 200

    def post(self):
        args = self.reqparse.parse_args()
        print (args)
        try:
            last_post_id = args.last_post_id
        except:
            last_post_id = None
        return contents(args.brand, last_post_id), 200

api.add_resource(InstAPI, '/api/v1/follow', endpoint='follow')
api.add_resource(InstContentsAPI, '/api/v1/contents', endpoint='contents')

if __name__ == '__main__':
    app.run(debug=True)
