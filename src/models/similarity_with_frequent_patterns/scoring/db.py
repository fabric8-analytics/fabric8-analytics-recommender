# This module contains database helper functions
# TODO: move away from low-level psycopg2; check out SQLAlchemy

from flask import g
import json
import psycopg2
import requests

from server import app

# construct DB connection string
_bayesian_graph_url = app.config['BAYESIAN_GRAPH_URL']


# TODO  - change the url as configuration parameter
def get_reference_stacks_from_graph(list_packages):
    # list_packages = ["path-type","core-util-is","node-uuid"]
    str_packages = ','.join(map(lambda x: "'" + x + "'", list_packages))
    payload = {'gremlin': "g.V().hasLabel('Version').has('pname', within(" + str_packages +
               ")).in('StackVersion').dedup().valueMap(true);"}
    response = requests.post(_bayesian_graph_url, data=json.dumps(payload))
    json_response = response.json()
    refstacks = json_response.get('result').get('data', [])
    # print(refstacks)
    list_ref_stacks = []
    if refstacks is not None:
        for refstack in refstacks:
            map_ref_stack = {}
            map_ref_stack['application_name'] = refstack.get('sname')[0]
            map_ref_stack['appstack_id'] = refstack.get('sid')[0]
            map_ref_stack['source'] = refstack.get('source')[0]
            map_ref_stack['usage'] = float(refstack.get('usage')[0])
            map_ref_stack['application_description'] = "Generated Stack: " + \
                                                       refstack.get('sname')[0]
            refstackid = refstack.get('id')
            print(refstackid)
            payload = {'gremlin': "g.V(" + str(refstackid) + ").out().valueMap()"}
            resp = requests.post(_bayesian_graph_url, data=json.dumps(payload))
            json_resp = resp.json()
            # print(json_resp)
            components = json_resp.get('result').get('data', [])

            if len(components) > 3 and len(components) < 9:
                # print(components)
                dependencies = []

                for component in components:
                    package = {}
                    version_spec = {}
                    package['package_name'] = component.get('pname')[0]
                    version_spec['spec'] = component.get('version')[0]
                    package['version_spec'] = version_spec
                    package['LOC'] = float(component.get('LOC')[0]) if ('LOC' in component) else 0
                    package['code_complexity'] = float(component.get('code_complexity')[0]) \
                        if 'code_complexity' in component else 0
                    package['is_downstream'] = component.get('is_downstream')[0] \
                        if 'is_downstream' in component else 'no'
                    dependencies.append(package)
                map_ref_stack['dependencies'] = dependencies
                # print(map_ref_stack)
                list_ref_stacks.append(map_ref_stack)
            # print(list_ref_stacks)
        return(list_ref_stacks)


def get_input_stacks_vectors_from_graph(inputList):
    inputStackList = []
    for package, version in inputList.items():
        if package is not None:
            payload = {'gremlin': "g.V().has('pecosystem','NPM').has('pname','" + package +
                       "').has('version','" + version + "').valueMap();"}
            resp = requests.post(_bayesian_graph_url, data=json.dumps(payload))
            resp_json = resp.json()
            # print(resp_json)
            if len(resp_json.get('result').get('data')) > 0:
                LOC = 0
                num_files = 0
                code_complexity = 0
                stackMap = {}
                stackMap['package_name'] = package
                stackMap['version'] = version
                if('LOC' in resp_json.get('result').get('data')[0]):
                    LOC = float(resp_json.get('result').get('data')[0].get('LOC')[0])
                if('num_files' in resp_json.get('result').get('data')[0]):
                    num_files = float(resp_json.get('result').get('data')[0].get('num_files')[0])
                if('code_complexity' in resp_json.get('result').get('data')[0]):
                    code_complexity = float(resp_json.get('result').get('data')[0]
                                            .get('code_complexity')[0])
                stackMap['LOC'] = LOC
                stackMap['num_files'] = num_files
                stackMap['code_complexity'] = code_complexity
                inputStackList.append(stackMap)
    return inputStackList
