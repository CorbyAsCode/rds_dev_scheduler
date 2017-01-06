

import boto3
import json
import os
import datetime

# Initialize boto objects
cf = boto3.client('cloudformation')
rds = boto3.client('rds')
s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')
now = datetime.datetime.now()
queried_rds_metadata = {}
dir_name = os.environ['S3_DIR_NAME']
rds_metadata_obj_name = dir_name + '/' + os.environ['RDS_METADATA_FILENAME']
app_lifecycle_tag = os.environ['APP_LIFECYCLE_TAG']
bucket_name = os.environ['S3_BUCKET_NAME']

#def delete_rds_stacks(event, context):
def delete_rds_stacks():

    try:
        all_db_instances = rds.describe_db_instances()
    except Exception, err:
        print "ERROR: Could not retreive all DB instances metadata: %s" % err
        
    for instance in all_db_instances['DBInstances']:
        arn = instance['DBInstanceArn']

        instance_tags = rds.list_tags_for_resource(ResourceName=arn)

        if len(instance_tags['TagList']) > 0:
            for tag in instance_tags['TagList']:
                if tag['Key'] == 'AWSService':
                    if tag['Value'] != app_lifecycle_tag:
                        pass

            queried_rds_metadata[instance['DBInstanceIdentifier']] = {}
            for key in instance.keys():
                queried_rds_metadata[instance['DBInstanceIdentifier']][key] = json_serial(instance[key])

    update_s3 = False
    for instance in queried_rds_metadata.keys():
        final_snapshot_id = instance + '-lifecycle-snapshot-' + '%s%02d%02d-%02d%02d%02d' % (now.year,
                                                                                                 now.month,
                                                                                                 now.day,
                                                                                                 now.hour,
                                                                                                 now.minute,
                                                                                                 now.second
                                                                                                )

        try:
            response = rds.delete_db_instance(
                           DBInstanceIdentifier=instance,
                           SkipFinalSnapshot=False,
                           FinalDBSnapshotIdentifier=final_snapshot_id
                       )

            if response:
                update_s3 = True
                print "NOTICE: Deleted instance: %s" % instance
            else:
                print "NOTICE: Did not delete instance: %s" % instance
        except Exception, err:
            print "ERROR: Could not delete instance %s: %s" % (instance, err)

    # Update the S3 RDS metadata filestore if we deleted a stack
    if update_s3:
        stringified_metadata = json.dumps(queried_rds_metadata, indent=4)

        try:
            response = s3_client.delete_object(Bucket=bucket_name, Key=rds_metadata_obj_name)
            try:
                response = s3_resource.Object(bucket_name, rds_metadata_obj_name).put(Body=stringified_metadata)
            except Exception, err:
                print "ERROR: Could not write new DB metadata to S3 object %s: %s" % (bucket_name+rds_metadata_obj_name, err)
        except Exception, err:
            print "ERROR: Could not delete old S3 DB metadata object %s: %s" % (bucket_name+rds_metadata_obj_name, err)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial
    else:
        return obj
    raise TypeError ("Type not serializable")

delete_rds_stacks()