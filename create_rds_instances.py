

import boto3
import json
import os
import datetime
import calendar

# Initialize boto objects 
s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')
rds = boto3.client('rds')
# Initialize variables
bucket_name = os.environ['S3_BUCKET_NAME']
dir_name = os.environ['S3_DIR_NAME']
rds_metadata_obj_name = dir_name + '/' + os.environ['RDS_METADATA_FILENAME']
app_lifecycle_tag = os.environ['APP_LIFECYCLE_TAG']
week_to_execute = os.environ['WEEK_TO_EXECUTE']
all_our_snapshots = []
s3_bucket = s3_resource.Bucket(bucket_name)
now = datetime.datetime.now()

#def create_rds_instances(event, context):
def create_rds_instances():

    if not check_week_number_of_month(now, week_to_execute):
        return

    # Get the previous RDS instance parameters from S3 as recorded by the delete process
    try:
        j = s3_client.get_object(Bucket=bucket_name, Key=rds_metadata_obj_name)['Body'].read()
    except Exception, err:
        print "ERROR: Error retreiving RDS instance metadata: %s" % err
        
    try:
        rds_instances_metadata = json.loads(j)
    except Exception, err:
        print "ERROR: Error converting S3 text file to dictionary: %s" % err

    for instance in rds_instances_metadata.keys():
        db_snapshot_identifier = ''
        db_instance_name = instance.lower()
        db_instance_identifier = rds_instances_metadata[instance]['DBInstanceIdentifier'].lower()
        snapshot_id_partial = db_instance_name + '-lifecycle-snapshot-'

        # Get all of this DB instance's snapshots
        try:
            snapshots = rds.describe_db_snapshots(DBInstanceIdentifier=db_instance_identifier)
        except Exception, err:
            print "ERROR: Error retreiving %s snapshots metadata: %s" % (db_instance_identifier, err)

        # Loop through all of this DB instance's snapshots to find one that was
        # created by RDS.
        # The delete process should keep the most recent RDS-created snapshot.
        for snapshot in snapshots['DBSnapshots']:
            if snapshot_id_partial in snapshot['DBSnapshotIdentifier']:
                all_our_snapshots.append(snapshot)

                db_snapshot_identifier = snapshot['DBSnapshotIdentifier']

        snapshot_dates = []
        for snapshot in all_our_snapshots:
            snapshot_dates.append(snapshot['SnapshotCreateTime'])

        print snapshot_dates
        snapshot_dates.sort()
        print snapshot_dates[-1]
        most_recent_snapshot_date = snapshot_dates[-1]

        for snapshot in all_our_snapshots:
            if snapshot['SnapshotCreateTime'] == most_recent_snapshot_date:
                db_snapshot_identifier = snapshot['DBSnapshotIdentifier']
        print "Latest snapshot date: %s, snapshot id: %s" % (most_recent_snapshot_date, db_snapshot_identifier)

        if not db_snapshot_identifier:
            print "DB snapshot partial name not found in list of snapshots: %s" % snapshot_id_partial
            continue

        restore_kwargs = {
            'DBInstanceIdentifier': rds_instances_metadata[instance]['DBInstanceIdentifier'],
            'DBSnapshotIdentifier': db_snapshot_identifier,
            'DBInstanceClass': rds_instances_metadata[instance]['DBInstanceClass'],
            'AvailabilityZone': rds_instances_metadata[instance]['AvailabilityZone'],
            'DBSubnetGroupName': rds_instances_metadata[instance]['DBSubnetGroup']['DBSubnetGroupName'],
            'MultiAZ': rds_instances_metadata[instance]['MultiAZ'],
            'PubliclyAccessible': rds_instances_metadata[instance]['PubliclyAccessible'],
            'AutoMinorVersionUpgrade': rds_instances_metadata[instance]['AutoMinorVersionUpgrade'],
            'StorageType': rds_instances_metadata[instance]['StorageType'],
            'Tags': [
                        {
                            "Key": "AppLifecycle",
                            "Value": app_lifecycle_tag
                        }
                    ],
            'CopyTagsToSnapshot': True
        }

        # Create the new instance using the DB snapshot if it exists.
        response = False
        try:
            #response = rds.restore_db_instance_from_db_snapshot(**restore_kwargs)
            print "NOTICE: Created DB Instance: %s from DB snapshot: %s" % (db_instance_name, db_snapshot_identifier)
        except Exception, err:
            print "ERROR: Error creating DB Instance %s: %s" % (db_instance_name, err)

def check_week_number_of_month(date_to_check, week_number):
    if str(week_number).lower() == 'all':
        return True
    elif str(week_number).lower() == 'first':
        week_index = 0
    elif str(week_number).lower() == 'last':
        week_index = -1
    else:
        week_index = int(week_number) - 1

    weeks_list = []
    cal = calendar.Calendar()
    weeks_of_month = cal.monthdayscalendar(date_to_check.year, date_to_check.month)
    for week in weeks_of_month:
        if 0 in week:
            continue
        else:
            weeks_list.append(week)

    if date_to_check.day in weeks_list[week_index]:
        return True
    else:
        return False

create_rds_instances()