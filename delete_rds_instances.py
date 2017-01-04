

import boto3
import json
import os
import datetime
import pprint

pp = pprint.PrettyPrinter(indent=4)

# Initialize boto objects
cf = boto3.client('cloudformation')
rds = boto3.client('rds')
s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')
now = datetime.datetime.now()
queried_rds_metadata = {}
region = os.environ['AWS_DEFAULT_REGION']
#account_id = context.invoked_function_arn.split(":")[4]
account_id = '332481357897'
dir_name = os.environ['S3_DIR_NAME']
rds_metadata_obj_name = dir_name + '/' + os.environ['RDS_METADATA_FILENAME']
rds_tag_value = os.environ['RDS_TAG_VALUE']
bucket_name = os.environ['S3_BUCKET_NAME']

#def delete_rds_stacks(event, context):
def delete_rds_stacks():

    try:
        all_db_instances = rds.describe_db_instances()
    except Exception, err:
        print "ERROR: Could not retreive all DB instances metadata: %s" % err
        
    for instance in all_db_instances['DBInstances']:
        arn = "arn:aws:rds:%s:%s:db:%s" % (region, account_id, instance['DBInstanceIdentifier'])
        instance_tags = rds.list_tags_for_resource(ResourceName=arn)

        if len(instance_tags['TagList']) > 0:
            for tag in instance_tags['TagList']:
                if tag['Key'] == 'AWSService':
                    if tag['Value'] != rds_tag_value:
                        pass

            for key in instance.keys():
                # Stopped here
                queried_rds_metadata[instance['DBInstanceIdentifier']][key] = json_serial(instance[key])
            #queried_rds_metadata[instance['DBInstanceIdentifier']]['Parameters'] = instance

            #for param in stack['Parameters']:
            #    if param['ParameterKey'] == 'DBInstanceName':
            #        queried_rds_metadata[stack['StackName']]['DBInstanceName'] = param['ParameterValue']

    update_s3 = False
    for instance in queried_rds_metadata.keys():
        response = False
        #db_instance_name = queried_rds_metadata[stack]['DBInstanceName']
        print queried_rds_metadata[instance]['InstanceCreateTime']

        '''
        try:
            db_metadata = rds.describe_db_instances(DBInstanceIdentifier=db_instance_name)
        except Exception, err:
            print "ERROR: Could not retreive instance metadata for %s: %s" % (db_instance_name, err)

        arn = "arn:aws:rds:%s:%s:db:%s" % (region, account_id, db_instance_name)
        instance_tags = rds.list_tags_for_resource(ResourceName=arn)
        for tag in instance_tags['TagList']:
            if 'Template' in tag['Key']:
                if tag['Value'] == 'RDS_PostgreSQL_CloudFormation_Template':
                    queried_rds_metadata[stack]['Template'] = tag['Value']
        '''

        final_snapshot_id = instance + '-lifecycle-snapshot-' + '%s-%02d-%s' % (now.day, now.month, now.year)

        '''
        try:
            response = rds.delete_db_instance(
                           DBInstanceIdentifier=instance,
                           SkipFinalSnapshot=False,
                           FinalDBSnapshotIdentifier=final_snapshot_id
                       )

            if response:
                update_s3 = True
                print "NOTICE: Deleted instance %s" % instance
            else:
                print "NOTICE: Did not delete instance %s" % instance
        except Exception, err:
            print "ERROR: Could not delete stack %s: %s" % (stack, err)
        '''
    # Update the S3 RDS metadata filestore if we deleted a stack
    #if update_s3:
        #print queried_rds_metadata

        pp.pprint(queried_rds_metadata)
        #stringified_metadata = json.dumps(queried_rds_metadata, indent=4)

        '''
        try:
            response = s3_client.delete_object(Bucket=bucket_name, Key=rds_metadata_obj_name)
            try:
                response = s3_resource.Object(bucket_name, s3_metadata_filename).put(Body=stringified_metadata)
            except Exception, err:
                print "ERROR: Could not write new DB metadata to S3 object %s: %s" % (bucket_name+s3_metadata_filename, err)
        except Exception, err:
            print "ERROR: Could not delete old S3 DB metadata object %s: %s" % (bucket_name+rds_metadata_obj_name, err)

        '''
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial
    else:
        return obj
    raise TypeError ("Type not serializable")

delete_rds_stacks()