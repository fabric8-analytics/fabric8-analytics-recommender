# @author - Saket Kumar Choudhary.
# This Code is meant to include similarity between two different versions of a
# package based on relative difference method.

from __future__ import division
from models.similarity_with_frequent_patterns.scoring.entities.entities import SimilarStack
from server import app


class RelativeSimilarity(object):
    def __init__(self):
        pass

    @classmethod
    def compare_version(self, ref_component_version, input_component_version):
        if ref_component_version.strip() == input_component_version.strip():
            return 1
        return 0

    @classmethod
    def relative_similarity(self, x, y):
        nu = sum(abs(a - b) for a, b in zip(x, y))
        dnu = sum(x) + sum(y)
        if dnu == 0:
            return 0
        diff = nu * 1.0 / dnu

        sim = round(1 - diff, 4)
        return sim

    @classmethod
    def get_refstack_component_list(self, ref_stack):
        refstack_component_list = []
        corresponding_version = []
        ref_stack_deps = ref_stack["dependencies"]
        if ref_stack_deps:
            for dependency in ref_stack_deps:
                refstack_component_list.append(dependency['package_name'])
                corresponding_version.append(dependency['version_spec']['spec'])
        return (refstack_component_list, corresponding_version)

    @classmethod
    def getp_value_graph(self, component_name, input_stack, ref_stack):
        distancevalue = 0.0
        pvalue = 0.0
        input_data = [0, 0, 0]
        ref_data = [0, 0, 0]
        for comp in input_stack:
            if(comp['package_name'] == component_name):
                inLOC = comp.get('LOC', 0)
                innum_files = comp.get('num_files', 0)
                incode_complexity = comp.get('code_complexity', 0)
                input_data = [inLOC, innum_files, incode_complexity]
                break

        for refcomp in ref_stack['dependencies']:
            if(refcomp['package_name'] == component_name):
                refLOC = refcomp.get('LOC', 0)
                refnum_files = refcomp.get('num_files', 0)
                refcode_complexity = refcomp.get('code_complexity', 0)
                ref_data = [refLOC, refnum_files, refcode_complexity]
                break

        pvalue = self.relative_similarity(input_data, ref_data)
        return pvalue

    @classmethod
    def downstream_boosting(self, missing_package_list, ref_stack, denominator):
        additional_downstream = 0.0
        missing_downstream_component = []
        for package in missing_package_list:
            for component in ref_stack['dependencies']:
                if component['package_name'] == package:
                    if component['is_downstream'] == 'yes':
                        additional_downstream = additional_downstream + 1.0
                        missing_downstream_component.append(package)
        return additional_downstream / denominator, missing_downstream_component

    @classmethod
    def compute_modified_jaccard_similarity(self, len_input_stack, len_ref_stack, vcount):
        return vcount / max(len_ref_stack, len_input_stack)

    def filter_package(self, input_stack, ref_stacks):
        '''Function applies Jaccard Similarity at Package Name only'''
        input_set = set(list(input_stack.keys()))
        jaccard_threshold = float(app.config['JACCARD_THRESHOLD'])
        filetered_ref_stacks = []
        original_score = 0.0
        for ref_stack in ref_stacks:
            vcount = 0
            refstack_component_list, corresponding_version = \
                self.get_refstack_component_list(ref_stack)
            refstack_component_set = set(refstack_component_list)
            vcount = len(input_set.intersection(refstack_component_set))
            # Get similarity of input stack w.r.t reference stack
            original_score = RelativeSimilarity.compute_modified_jaccard_similarity(
                len(input_set), len(refstack_component_list), vcount)
            if original_score > jaccard_threshold:
                filetered_ref_stacks.append(ref_stack)
        return filetered_ref_stacks

    def find_relative_similarity(self, input_stack, input_stack_vectors, filtered_ref_stacks):
        '''Function for Relative Similarity'''
        input_set = set(list(input_stack.keys()))
        similarity_score_threshold = float(app.config['SIMILARITY_SCORE_THRESHOLD'])
        similar_stack_lists = []
        max_sim_score = 0.0
        boosted_score_list = []
        for ref_stack in filtered_ref_stacks:
            missing_package_list = []
            missing_package_version = []
            version_mismatch_list = []
            vcount = 0
            refstack_component_list, corresponding_version = \
                self.get_refstack_component_list(ref_stack)
            refstack_component_set = set(refstack_component_list)
            for component, ref_stack_component_version in zip(refstack_component_list,
                                                              corresponding_version):
                if component in input_stack:
                    input_component_version = input_stack[component]
                    if (self.compare_version(ref_stack_component_version, input_component_version)):
                        vcount = vcount + 1
                    else:
                        version_mismatch_list.append(component)
                        vcount = vcount + self.getp_value_graph(component, input_stack_vectors,
                                                                ref_stack)
                else:
                    missing_package_list.append(component)
                    missing_package_version.append(ref_stack_component_version.strip())

            original_score = self.compute_modified_jaccard_similarity(len(input_set),
                                                                      len(refstack_component_list),
                                                                      vcount)
            # Get Downstream Boosting
            boosted_score, missing_downstream_component = self.downstream_boosting(
                missing_package_list, ref_stack, max(len(input_set), len(refstack_component_list)))
            downstream_score = original_score + boosted_score
            if original_score > max_sim_score:
                max_sim_score = original_score
            if(original_score > similarity_score_threshold):
                objid = str(ref_stack["appstack_id"])
                usage_score = ref_stack["usage"] if "usage" in ref_stack else None
                source = ref_stack["source"] if "source" in ref_stack else None
                similar_stack = SimilarStack(objid, usage_score, source, original_score,
                                             downstream_score, missing_package_list,
                                             version_mismatch_list, missing_downstream_component)
                similar_stack_lists.append(similar_stack)
        return similar_stack_lists
