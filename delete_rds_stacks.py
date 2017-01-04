

import boto3
import json
import os

# Need to modify this so it uses RDS calls intead of CF calls

# Initialize boto objects
cf = boto3.client('cloudformation')
rds = boto3.client('rds')
s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')
queried_rds_metadata = {}
region = os.environ['AWS_DEFAULT_REGION']
#account_id = context.invoked_function_arn.split(":")[4]
account_id = '332481357897'
dir_name = os.environ['S3_DIR_NAME']
rds_metadata_obj_name = dir_name + '/' + os.environ['RDS_METADATA_FILENAME']
cf_rds_tag_value = os.environ['CF_RDS_TAG_VALUE']
bucket_name = os.environ['S3_BUCKET_NAME']

#def delete_rds_stacks(event, context):
def delete_rds_stacks():


    try:
        all_stacks = cf.describe_stacks()
    except Exception, err:
        print "ERROR: Could not retreive all CF stacks metadata: %s" % err
        
    for stack in all_stacks['Stacks']:
        if len(stack['Tags']) > 0:
            for tag in stack['Tags']:
                if tag['Key'] == 'AWSService':
                    if tag['Value'] != cf_rds_tag_value:
                        pass

        queried_rds_metadata[stack['StackName']] = {}
        queried_rds_metadata[stack['StackName']]['Parameters'] = stack['Parameters']
        for param in stack['Parameters']:
            if param['ParameterKey'] == 'DBInstanceName':
                queried_rds_metadata[stack['StackName']]['DBInstanceName'] = param['ParameterValue']

    update_s3 = False
    for stack in queried_rds_metadata.keys():
        response = False
        db_instance_name = queried_rds_metadata[stack]['DBInstanceName']
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
        try:
            response = cf.delete_stack(StackName=stack)
            update_s3 = True
            print "NOTICE: Deleted stack %s" % stack
        except Exception, err:
            print "ERROR: Could not delete stack %s: %s" % (stack, err)

    # Update the S3 RDS metadata filestore if we deleted a stack
    if update_s3:
        stringified_metadata = json.dumps(queried_rds_metadata, indent=4)
        try:
            response = s3_client.delete_object(Bucket=bucket_name, Key=rds_metadata_obj_name)
            try:
                response = s3_resource.Object(bucket_name, s3_metadata_filename).put(Body=stringified_metadata)
            except Exception, err:
                print "ERROR: Could not write new DB metadata to S3 object %s: %s" % (bucket_name+s3_metadata_filename, err)
        except Exception, err:
            print "ERROR: Could not delete old S3 DB metadata object %s: %s" % (bucket_name+rds_metadata_obj_name, err)


delete_rds_stacks()