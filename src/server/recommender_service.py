"""Implementation of reccomender service."""

import json
from models.similarity_with_frequent_patterns.scoring import db
from models.similarity_with_frequent_patterns.scoring.similarity import relativesimilarity


class RecommenderService(object):
    """Implementation of reccomender service."""

    def __init__(self):
        """Construct new instance of this class."""
        pass

    def generate_recommendations_for(self, input_manifest):
        """Generate recommendations for provided manifest file."""
        input_stack = {d.package_name: d.version_spec.spec for d in input_manifest.dependencies}
        rs = relativesimilarity.RelativeSimilarity()
        # Read data from Graph
        # Get Input Stack data
        inputStackVectors = db.get_input_stacks_vectors_from_graph(input_stack)
        ref_stacks = db.get_reference_stacks_from_graph(input_stack.keys())
        # First Filter working at package level
        filtered_ref_stacks = rs.filter_package(input_stack, ref_stacks)
        # Relative Similarity Measure
        similar_stacks_list = rs.find_relative_similarity(input_stack, inputStackVectors,
                                                          filtered_ref_stacks)
        similarity_list = self._get_stack_values(similar_stacks_list)
        result = {"recommendations": {
                     "similar_stacks": similarity_list,
                     "component_level": None,
                 }}
        return result

    def _get_stack_values(self, similar_stacks_list):
        similarity_list = []
        for stack in similar_stacks_list:
            s_stack = {
                "stack_id": stack.stack_id,
                "similarity": stack.downstream_score,
                "original_score": stack.original_score,
                "usage": stack.usage_score,
                "source": stack.source,
                "analysis": {
                    "missing_downstream_component": stack.downstream_component,
                    "missing_packages": stack.missing_packages,
                    "version_mismatch": stack.version_mismatch
                }
            }
            similarity_list.append(s_stack)
        return similarity_list
