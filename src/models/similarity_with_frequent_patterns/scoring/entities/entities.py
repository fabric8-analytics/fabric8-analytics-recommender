import os
import json
import re
import time
import datetime


def default_json_decoder(self):
    return self.__dict__


class User(object):
    pass


class AppStack(object):
    def __init__(self, name="", version="", description="", dependencies=[]):
        self.appstack_id = None
        self.application_name = name
        self.application_version = version
        self.application_description = description
        self.dependencies = dependencies
        #add isrefstack attribute

    @classmethod
    def read_from_file(self, fname):
        data = None
        with open(os.path.abspath(fname)) as f:
            data = json.load(f)
        return self.read_from_dict(data)

    @classmethod
    def read_from_dict(self, data):
        if data is None:
            return None

        name = data['name']
        description = data['description']
        version = data['version']
        dependencies = []

        for k,v in data['dependencies'].items():
            dname = k
            dversion = v
            dependencies.append(Dependency(dname, dversion))

        return AppStack(name, version, description, dependencies)


    @classmethod
    def has_version_val(self, vspec):
        return(Version(vspec))

    def has_dependencies(self, n, s, v):
        return any(
            d.package_name == n and d.version_spec.spec == s and
            AppStack.has_version_val(d.version_spec.spec).version == v for d in self.dependencies)

    def return_json(self):
        return json.dumps(self, default=default_json_decoder)


class Dependency(object):
    def __init__(self, dname, dversion):
        self.package_name = dname
        self.version_spec = VersionSpec(dversion)  # this is an object of VersionSpec type


class VersionSpec(object):
    def __init__(self, dversion):
        self.spec = dversion  # this is the version spec


class Version(object):
    def __init__(self, vspec):
        value = re.sub('[><=^vx]', '', vspec)
        if value[-1] == '.':
            value = value[:-1]
        self.version = value  # this is the version


class Recommendations(object):
    def __init__(self, similar_stacks=[], guidance=[], frequently_used=[]):
        self.similar_stacks = similar_stacks
        self.package_guidance = guidance
        self.frequently_used = frequently_used

    def return_json(self):
        return json.dumps(self, default=default_json_decoder)


class SimilarStack(object):

    def __init__(self, stack_id, usage_score=None, source= None, original_score=None, downstream_score=None, missing_packages=[], version_mismatch=[],downstream_component = []):
        self.stack_id = stack_id
        self.usage_score = usage_score
        self.source = source
        self.original_score = original_score
        self.downstream_score = downstream_score
        self.missing_packages = missing_packages
        self.version_mismatch = version_mismatch
        self.downstream_component = downstream_component

    def __repr__(self):
        return '{}: {} {}'.format(self.__class__.__name__,self.stack_id,self.similarity_score)

    def __cmp__(self, other):
        if hasattr(other, 'getKey'):
            return self.getKey().__cmp__(other.getKey())

    def getKey(self):
        return self.similarity_score

    def return_json(self):
        return json.dumps(self, default=default_json_decoder)


class PackageGuidance(object):
    def __init__(self, package_id, reason, our_guidance):
        self.package_id = package_id
        self.reason = reason
        self.our_guidance = our_guidance


class StackActivity(object):
    def __init__(self, stack_id, activity_done, date_val):
        self.stack_id = stack_id
        self.activity_done = activity_done
        self.timestamp = time.mktime(datetime.datetime.strptime(date_val, "%Y-%m-%dT%H.%M.%S").timetuple())
