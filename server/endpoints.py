"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
from http import HTTPStatus

from flask import Flask, request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS

import werkzeug.exceptions as wz

import states.query as sqry

app = Flask(__name__)
CORS(app)
api = Api(app)

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'
HELLO_EP = '/hello'
HELLO_RESP = 'hello'
STATES_EP = '/states'
STATES_RESP = 'States:'
MESSAGE = 'Message'


@api.route(HELLO_EP)
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {}
        # return {HELLO_RESP: 'world'}


@api.route(ENDPOINT_EP)
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        endpoints = sorted(rule.rule for rule in api.app.url_map.iter_rules())
        return {"Available endpoints": endpoints}


STATE_CREATE_FLDS = api.model('CreateState', {
    'state_code': fields.String(required=True),
    'population': fields.Integer(required=True),
    'capital': fields.String(required=True),
    'area_sq_miles': fields.Float(required=True),
    'name': fields.String(required=True),
})


@api.route(STATES_EP)
class States(Resource):
    """
    The get method will return a list of all states in the database.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        The get method will return a list of all states in the database.
        """
        states = sqry.read()
        if states is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {STATES_RESP: states}

    @api.expect(STATE_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED.value, 'Created')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def post(self):
        """
        Add a new state.
        """
        data = request.get_json(silent=True) or {}
        try:
            new_state = sqry.create(data.get('state_code'),
                                    data.get('population'),
                                    data.get('capital'),
                                    data.get('area_sq_miles'),
                                    data.get('name'))
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if new_state is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {MESSAGE: 'State added.', STATES_RESP: new_state}, \
            HTTPStatus.CREATED
