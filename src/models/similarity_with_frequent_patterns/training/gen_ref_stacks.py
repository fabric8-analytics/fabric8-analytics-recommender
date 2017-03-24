# Imports
from pyspark import SparkConf, SparkContext
from pyspark.mllib.fpm import FPGrowth
from pyspark.sql import SQLContext
from pyspark.sql import Row

from operator import add
import sys
import json
import requests
import random
from uuid import uuid4

# TODOs:
# 1. Currently ecosystem is set as 'trial', but we need to extract ecosystem from input S3 data

# Constants
APP_NAME = "GenerateReferenceStacks"
MAX_WIDTH = 100  # Max number of packages/components allowed in a transaction


# OTHER FUNCTIONS/CLASSES
def extract_ecosystem(data):
    return [] if data is None else map(lambda x: x.get("ecosystem"), data)


def map_package_versions(json_data):
    if json_data is None:
        return []
    else:
        # select only npm entries
        npm_entries = filter(lambda x: x.get("ecosystem") in ['NPM', 'NPM Dist'], json_data)
        # name version
        results = filter(lambda y: y is not None, map(lambda x: x.get("result"), npm_entries))
        package_name_version = map(lambda z: (z.get("name"), z.get("version")), results)
        return filter(lambda x: None not in x, package_name_version)


def freqItemsetToRefStack(freqItemset, freq):
    ref_stack = {}  # Empty map
    if freqItemset is not None:
        pv_list = map(lambda x: x.split("@@"), freqItemset)
        pk_names = map(lambda x: x[0], pv_list)
        stack_name = "-".join(pk_names)
        stack_version = "1.0"
        stack_description = "Generated stack: %s" % (stack_name,)
        stack_deps = dict(pv_list)
        stack_license = "Apache-2.0"
        stack_source = "OpenShiftV2"
        stack_ecosystem = "NPM"
        ref_stack = {
            "ecosystem": stack_ecosystem,
            "name": stack_name,
            "version": stack_version,
            "description": stack_description,
            "dependencies": stack_deps,
            "license": stack_license,
            "usage": freq,
            "source": stack_source,
            "is_ref_stack": 'true'
        }
    return ref_stack


def fire_gremlin(gremlin_server, str_gremlin):
    payload = {'gremlin': str_gremlin}
    response = requests.post(gremlin_server, data=json.dumps(payload))

    # TODO: check for error and raise exception
    if response.status_code != 200:
        print ("ERROR %d: %s") % (response.status_code, response.reason)

    json_response = response.json()
    print json_response


def gremlin_str_pkg_version(ecosystem, pkg_name, version):
    return """insert_package_version(g, '{}', '{}', '{}');
    """.format(ecosystem, pkg_name, version)


def gremlin_str_ref_stack(ref_stack):
    stack_name = ref_stack.get('name')
    eco_system = 'trial'
    usage = ref_stack.get('usage')
    source = ref_stack.get('source')
    is_ref_stack = ref_stack.get('is_ref_stack')
    sid = uuid4().hex
    tmp_list = map(lambda x: "'{}':'{}'".format(x[0], x[1]), ref_stack.get('dependencies').items())
    dependencies = "[" + ','.join(tmp_list) + "]"
    return """insert_ref_stack(g, '{}', '{}', '{}', '{}', '{}', '{}', {});
    """.format(sid, stack_name, eco_system, usage, source, is_ref_stack, dependencies)



def main(sc, src_s3_bucket, target_gremlin_server):
    gremlin_method_insert_pkg_version =  """
        def insert_package_version(g, ecosystem, name, version) {
        def pred_pkg = g.V().has('vertex_label', 'Package').has('name', name).has('ecosystem', ecosystem);
        def pkg_vertex = (pred_pkg.hasNext()) ? pred_pkg.next() : g.addV('vertex_label', 'Package', 'name', name, 'ecosystem', ecosystem).next()

        def pred_version = g.V().has('vertex_label', 'Version').has('pecosystem', ecosystem).has('pname', name).has('version', version);
        if (!pred_version.hasNext()) {
            def version_vertex = g.addV('vertex_label', 'Version', 'pecosystem', ecosystem, 'pname', name, 'version', version).next();
            pkg_vertex.addEdge('has_version', version_vertex);
        }
    }
    """

    gremlin_method_insert_ref_stack = """
    def insert_ref_stack(g, sid, sname, secosystem, usage, source, is_ref_stack, dependencies) {
        def pred_stack = g.V().has('vertex_label', 'Stack').has('sname', sname).has('secosystem', secosystem)
        if (!pred_stack.hasNext()) {
            def stack_vertex = g.addV('vertex_label','Stack','sname', sname, 'secosystem', secosystem, 'usage', usage, 'source', source, 'is_ref_stack', is_ref_stack, 'sid', sid).next();

            for (k in dependencies.keySet()) {
                def version_vertex = g.V().has('vertex_label', 'Version').has('pecosystem', secosystem).has('pname', k).has('version', dependencies.get(k)).next();
                stack_vertex.addEdge('has_dependency', version_vertex);
            }
        }
    }
    """

    sqlContext = SQLContext(sc)
    input_data = sc.wholeTextFiles("s3n://" + src_s3_bucket + "/")

    not_null_data = input_data.filter(lambda x: x[1].strip() not in ['null', ''])
    json_formatted = not_null_data.map(lambda x: (x[0], json.loads(x[1])))

    only_npm = json_formatted.filter(lambda x: 'NPM' in extract_ecosystem(x[1]))
    package_versions = only_npm.map(lambda x: (x[0], map_package_versions(x[1])))
    non_fail_package_versions = package_versions.map(
        lambda x: (x[0], filter(lambda pv: pv[0] != 'fail' and pv[1] != 'fail', x[1])))
    non_empty_package_versions = non_fail_package_versions.filter(lambda x: len(x[1]) > 0)

    transactions = non_empty_package_versions.map(lambda x: map(lambda pv: "%s@@%s" % (pv[0], pv[1]), x[1]))
    unique_transactions = transactions.map(lambda x: list(set(x)))
    truncated_transactions = unique_transactions.map(lambda x: x[:MAX_WIDTH]).cache()
    count_transactions = truncated_transactions.count()
    model = FPGrowth.train(truncated_transactions,
                           minSupport=0.5, numPartitions=truncated_transactions.getNumPartitions())
    rddJsons = model.freqItemsets().map(
        lambda x: freqItemsetToRefStack(x.items, float(x.freq) / float(count_transactions)))
    # rddJsons = rddRefStacks.filter(lambda x: len(x.get('dependencies').items()) > 4 and len(x.get('dependencies').items()) <= 10 )

    # Save packages and versions
    rddVersions = rddJsons.flatMap(lambda x: x.get('dependencies').items())
    dfVersions = rddVersions.toDF().distinct()
    rddGremlinVersions = dfVersions.rdd.map(lambda x: gremlin_str_pkg_version('trial', x[0], x[1]))
    str_gremlin = gremlin_method_insert_pkg_version + ' '.join(rddGremlinVersions.collect())
    fire_gremlin(target_gremlin_server, str_gremlin)

    # Save stacks
    rdd_gremlin_stacks = rddJsons.map(lambda x: gremlin_str_ref_stack(x))
    str_gremlin = gremlin_method_insert_ref_stack + ' '.join(rdd_gremlin_stacks.collect())
    fire_gremlin(target_gremlin_server, str_gremlin)


if __name__ == "__main__":

    # Configure Spark
    conf = SparkConf().setAppName(APP_NAME)
    sc = SparkContext(conf=conf)

    # Gather input arguments
    if len(sys.argv) < 3:
        usage = """
        spark-submit <spark-options> gen_ref_stacks.py <src_s3_bucket> <target_gremlin_server>
        where
        src_s3_bucket = s3 bucket to read input data from
        target_gremlin_server = target gremlin server to be populated with reference stacks
        """

        example = """
        spark-submit gen_ref_stacks.py mitesh-subset-v2 http://localhost:8182
        """
        print("Insufficient arguments!")
        print("Usage: %s", usage)
        print("Example: %s", example)
        sys.exit(1)

    src_s3_bucket = sys.argv[1]
    target_gremlin_server = sys.argv[2]

    # Execute Main functionality
    main(sc, src_s3_bucket, target_gremlin_server)
