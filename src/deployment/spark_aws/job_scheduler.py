"""Script to schedule training job."""

import submit_training_job

if __name__ == "__main__":
    src_code_file = "/gen_ref_stacks.py"
    submit_training_job.run(src_code_file)
