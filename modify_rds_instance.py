import boto3
import os
import json

rds = boto3.client('rds')
s3_client = boto3.client('s3')

# Initialize variables
bucket_name = os.environ['S3_BUCKET_NAME']
dir_name = os.environ['S3_DIR_NAME']
rds_metadata_obj_name = dir_name + '/' + os.environ['RDS_METADATA_FILENAME']

def modify_instance(event, context):
    message = event['Records'][0]['Sns']['Message']

    for pair in message.split(','):
        if 'Event Source' in pair:
            event_source = str(pair.split(':')[1].strip('{').strip('}').strip('"'))
        if 'Event Message' in pair:
            event_message = str(pair.split(':')[1].strip('{').strip('}').strip('"'))
        if 'Source ID' in pair:
            db_instance_id = str(pair.split(':')[1].strip('{').strip('}').strip('"'))

    if not 'Restored from snapshot' in event_message and \
        not '-lifecycle-snapshot-' in event_message:
        print "NOTICE: This is not the message we're looking for...exiting"
        return
    else:
        print "NOTICE: This is the message we're looking for...continuing"

    # Get the previous RDS instance parameters from S3 as recorded by the delete process
    try:
        j = s3_client.get_object(Bucket=bucket_name, Key=rds_metadata_obj_name)['Body'].read()
    except Exception, err:
        print "ERROR: Error retreiving RDS instance metadata from Bucket: %s, Key: %s: %s" % (bucket_name, rds_metadata_obj_name, err)
        return

    try:
        rds_instances_metadata = json.loads(j)
    except Exception, err:
        print "ERROR: Error converting S3 text file to dictionary: %s" % err
        return

    db_security_groups = [sg['VpcSecurityGroupId'] for sg in rds_instances_metadata[db_instance_id]['VpcSecurityGroups']]

    try:
        response = rds.modify_db_instance(
            ApplyImmediately=True,
            DBInstanceIdentifier=db_instance_id,
            VpcSecurityGroupIds=db_security_groups
        )
    except Exception, err:
        print "ERROR: Could not modify DB instance '%s': %s" % (db_instance_id, err)

