import flask
import json
import sys
import codecs
import logging
import urllib
from flask import Flask, request, redirect, make_response
from flask_cors import CORS
from server.recommender_service import RecommenderService
from models.similarity_with_frequent_patterns.scoring.entities.entities import AppStack
from server import app

logging.basicConfig(filename='error.log', level=logging.DEBUG)
app = Flask(__name__)
app.config.from_object('server.config')
CORS(app)

# Python2.x: Make default encoding as UTF-8
if sys.version_info.major == 2:
    reload(sys)
    sys.setdefaultencoding('UTF8')


########################################
# ROUTES: /api/v1.0
#
# POST /recommendation
# GET /recommendation/<recommendation-id> (for later)
########################################


# Reference: http://flask.pocoo.org/snippets/117/
def list_routes(app):
    output = []
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        url = flask.url_for(rule.endpoint, **options)
        output.extend([{
                           "endpoint_name": rule.endpoint,
                           "method": m,
                           "url": urllib.unquote(url)
                       } for m in rule.methods if m in ["GET", "POST", "PUT", "DELETE"]])
    return output


@app.errorhandler(404)
def not_found(error):
    return make_response(flask.jsonify({'error': 'URL NOT FOUND'}), 404)


@app.route('/')
def index():
    return redirect('/api/v1.0/')


@app.route('/api/v1.0/')
def apis_index():
    app.logger.info("APIs main")
    routes_list = list_routes(app)
    return flask.jsonify({
        "routes_list": routes_list
        })

@app.route('/api/v1.0/recommendation', methods=['POST'])
def get_recommendation():
    f = request.files['packagejson']
    file_name = f.filename
    if file_name == '':
        return redirect('/')
    reader = codecs.getreader('utf-8')
    json_data = json.load(reader(f))
    input_stack = AppStack.read_from_dict(json_data)
    recsvc = RecommenderService()
    result = recsvc.generate_recommendations_for(input_stack)
    return flask.jsonify(result)


@app.route('/api/v1.0/recommendation/<appstack_id>', methods=['GET'])
def get_recommendation_for(appstack_id):
    #recsvc = RecommenderService()
    #data = recsvc.load_recommendation_for(appstack_id)
    #if data is not None:
    #    return flask.jsonify(data)
    #else:
    #    return flask.jsonify({"ERROR": "No such AppStack with ID: %s" % (appstack_id, )})
    return ({"ERROR": "No such API endpoint implemented"})

if __name__ == "__main__":
    app.run()
