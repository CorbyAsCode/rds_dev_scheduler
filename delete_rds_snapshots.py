
import boto3
import datetime
import pytz

rds = boto3.client('rds')

# Initialize variables as empty strings
event_source = current_db_snapshot_id = event_message = old_snapshot = db_instance_name = ''

def delete_rds_snapshots():

    now = datetime.datetime.now()
    now = now.replace(tzinfo=pytz.utc)
    one_week = datetime.timedelta(weeks=7)
    date_7_days_ago = now - one_week

    # For testing...
    one_hour = datetime.timedelta(hours=3)
    last_hour = now - one_hour

    # Query for all of the DB snapshots
    try:
        all_snapshots = rds.describe_db_snapshots()['DBSnapshots']
    except Exception, err:
        print "ERROR: Could not retrieve snapshot metadata: %s" % err
        return
    
    # If no other snapshots are found, we can stop here
    if len(all_snapshots) == 0:
        return
    
    # Loop through all snapshots to see which ones need deleted
    for snapshot in all_snapshots:
        snap_timestamp = snapshot['SnapshotCreateTime']
        print snap_timestamp
        snap_id = snapshot['DBSnapshotIdentifier']

        if '-lifecycle-snapshot-' in snap_id:
            #if snap_timestamp < date_7_days_ago:
            if snap_timestamp < last_hour:
                try:
                    response = rds.delete_db_snapshot(DBSnapshotIdentifier=snap_id)
                    print "Deleted snapshot '%s'" % snap_id
                except Exception, err:
                    print "ERROR: Could not delete DB snapshot %s: %s" % (snap_id, err)


delete_rds_snapshots()