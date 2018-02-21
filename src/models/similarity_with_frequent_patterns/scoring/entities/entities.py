"""Definition of entities used during analysis."""

import os
import json
import re
import time
import datetime


def default_json_decoder(self):
    """Provide the encoder for JSON data."""
    return self.__dict__


class User(object):
    """Class User."""

    pass


class AppStack(object):
    """AppStack class."""

    def __init__(self, name="", version="", description="", dependencies=[]):
        """Construct an instance of the AppStack class."""
        self.appstack_id = None
        self.application_name = name
        self.application_version = version
        self.application_description = description
        self.dependencies = dependencies
        # add isrefstack attribute

    @classmethod
    def read_from_file(self, fname):
        """Read appStack attributes from given file."""
        data = None
        with open(os.path.abspath(fname)) as f:
            data = json.load(f)
        return self.read_from_dict(data)

    @classmethod
    def read_from_dict(self, data):
        """Read appStack attributes from given dictionary."""
        if data is None:
            return None

        name = data['name']
        description = data['description']
        version = data['version']
        dependencies = []

        for k, v in data['dependencies'].items():
            dname = k
            dversion = v
            dependencies.append(Dependency(dname, dversion))

        return AppStack(name, version, description, dependencies)

    @classmethod
    def has_version_val(self, vspec):
        """Return version for given spec, if exists."""
        return(Version(vspec))

    def has_dependencies(self, n, s, v):
        """Return dependencies, if exists."""
        return any(
            d.package_name == n and d.version_spec.spec == s and
            AppStack.has_version_val(d.version_spec.spec).version == v for d in self.dependencies)

    def return_json(self):
        """Return attributes in form of JSON data."""
        return json.dumps(self, default=default_json_decoder)


class Dependency(object):
    """Dependency class."""

    def __init__(self, dname, dversion):
        """Construct an instance of the Dependency class."""
        self.package_name = dname
        self.version_spec = VersionSpec(dversion)  # this is an object of VersionSpec type


class VersionSpec(object):
    """VersionSpec class."""

    def __init__(self, dversion):
        """Construct an instance of the VersionSpec class."""
        self.spec = dversion  # this is the version spec


class Version(object):
    """Version class."""

    def __init__(self, vspec):
        """Construct an instance of the Version class."""
        value = re.sub('[><=^vx]', '', vspec)
        if value[-1] == '.':
            value = value[:-1]
        self.version = value  # this is the version


class Recommendations(object):
    """Recommendations class."""

    def __init__(self, similar_stacks=[], guidance=[], frequently_used=[]):
        """Construct an instance of the Recommendations class."""
        self.similar_stacks = similar_stacks
        self.package_guidance = guidance
        self.frequently_used = frequently_used

    def return_json(self):
        """Return attributes in form of JSON data."""
        return json.dumps(self, default=default_json_decoder)


class SimilarStack(object):
    """SimilarStack class."""

    def __init__(self, stack_id, usage_score=None, source=None, original_score=None,
                 downstream_score=None, missing_packages=[], version_mismatch=[],
                 downstream_component=[]):
        """Construct an instance of the SimilarStack class."""
        self.stack_id = stack_id
        self.usage_score = usage_score
        self.source = source
        self.original_score = original_score
        self.downstream_score = downstream_score
        self.missing_packages = missing_packages
        self.version_mismatch = version_mismatch
        self.downstream_component = downstream_component

    def __repr__(self):
        """Return textual representation of an instance of SimilarStack class."""
        return '{}: {} {}'.format(self.__class__.__name__, self.stack_id, self.similarity_score)

    def __cmp__(self, other):
        """Compare two instances of SimilarStack class."""
        if hasattr(other, 'getKey'):
            return self.getKey().__cmp__(other.getKey())

    def getKey(self):
        """Return the similarity score."""
        return self.similarity_score

    def return_json(self):
        """Return attributes in form of JSON data."""
        return json.dumps(self, default=default_json_decoder)


class PackageGuidance(object):
    """PackageGuidance class."""

    def __init__(self, package_id, reason, our_guidance):
        """Construct an instance of the PackageGuidance class."""
        self.package_id = package_id
        self.reason = reason
        self.our_guidance = our_guidance


class StackActivity(object):
    """StackActivity class."""

    def __init__(self, stack_id, activity_done, date_val):
        """Construct an instance of the StackActivity class."""
        self.stack_id = stack_id
        self.activity_done = activity_done
        self.timestamp = time.mktime(datetime.datetime.strptime(date_val,
                                                                "%Y-%m-%dT%H.%M.%S").timetuple())
