# ----------------------------------------------------------------------------------------------------------------------
# This script spawns a spark emr cluster on AWS and submits a job to run the given src code.
#
# Dependency: It requires boto3 library.
#
# Reference:
#    http://stackoverflow.com/questions/36706512/how-do-you-automate-pyspark-jobs-on-emr-using-boto3-or-otherwise
#
# TODO:
# 1. Improve error handling
# ----------------------------------------------------------------------------------------------------------------------
import sys
import boto3
from time import gmtime, strftime
import config


def run(input_src_code_file):
    str_cur_time = strftime("%Y_%m_%d_%H_%M_%S", gmtime())

    # S3 bucket/key, where the input spark job ( src code ) will be uploaded
    s3_bucket = config.DEPLOYMENT_PREFIX + '-automated-analytics-spark-jobs'
    s3_key = config.DEPLOYMENT_PREFIX + '_spark_job.py'
    s3_uri = 's3://{bucket}/{key}'.format(bucket=s3_bucket, key=s3_key)

    # S3 bucket/key, where the spark job logs will be maintained
    # Note: these logs are AWS logs that tell us about application-id of YARN application
    #       we need to log into EMR cluster nodes and use application-id to view YARN logs
    s3_log_bucket = config.DEPLOYMENT_PREFIX + '-automated-analytics-spark-jobs'
    s3_log_key = config.DEPLOYMENT_PREFIX + '_spark_emr_log_' + str_cur_time + '/'
    s3_log_uri = 's3://{bucket}/{key}'.format(bucket=s3_log_bucket, key=s3_log_key)

    print "Uploading the src code to AWS S3 URI " + s3_uri + " ..."
    # Note: This overwrites if file already exists
    s3_client = boto3.client('s3',
                             aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    s3_client.upload_file(input_src_code_file, s3_bucket, s3_key)

    print "Starting spark emr cluster and submitting the jobs ..."
    emr_client = boto3.client('emr',
                              aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                              region_name='us-east-1')
    response = emr_client.run_job_flow(
        Name=config.DEPLOYMENT_PREFIX + "_automated_cluster_" + str_cur_time,
        LogUri=s3_log_uri,
        ReleaseLabel='emr-5.2.1',
        Instances={
            'MasterInstanceType': 'm3.xlarge',
            'SlaveInstanceType': 'm3.xlarge',
            'InstanceCount': 3,
            'KeepJobFlowAliveWhenNoSteps': False,
            'TerminationProtected': False,
            'Ec2SubnetId': 'subnet-50271f16',
            'Ec2KeyName': 'Zeppelin2Spark'
        },
        Applications=[
            {
                'Name': 'Spark'
            }
        ],
        BootstrapActions=[
            {
                'Name': 'Maximize Spark Default Config',
                'ScriptBootstrapAction': {
                    'Path': 's3://support.elasticmapreduce/spark/maximize-spark-default-config',
                }
            },
        ],
        Steps=[
        {
            'Name': 'Setup Debugging',
            'ActionOnFailure': 'TERMINATE_CLUSTER',
            'HadoopJarStep': {
                'Jar': 'command-runner.jar',
                'Args': ['state-pusher-script']
            }
        },
        {
            'Name': 'setup - copy files',
            'ActionOnFailure': 'CANCEL_AND_WAIT',
            'HadoopJarStep': {
                'Jar': 'command-runner.jar',
                'Args': ['aws', 's3', 'cp', s3_uri, '/home/hadoop/']
            }
        },
        {
            'Name': 'Run Spark',
            'ActionOnFailure': 'CANCEL_AND_WAIT',
            'HadoopJarStep': {
                'Jar': 'command-runner.jar',
                'Args': ['spark-submit', '/home/hadoop/' + s3_key, config.AWS_BUCKET, config.GREMLIN_SERVER_URL_REST]
            }
        }
        ],
        VisibleToAllUsers=True,
        JobFlowRole='EMR_EC2_DefaultRole',
        ServiceRole='EMR_DefaultRole'
    )

    if response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
        print "Done! The cluster was submitted successfully! Job flow id is " + response.get('JobFlowId')
    else:
        print "Error! The job/cluster could not be created!"
        print response


if __name__ == "__main__":
    # Gather input arguments
    if len(sys.argv) < 2:
        usage = sys.argv[0] + " <src_code_file> \n"
        example = sys.argv[0] + " gen_ref_stacks.py \n"
        print("Error: Insufficient arguments!")
        print("Usage: " + usage)
        print("Example: " + example)
        sys.exit(1)

    src_code_file = sys.argv[1]
    run(src_code_file)

