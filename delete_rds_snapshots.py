
import boto3
import datetime
import pytz
import os

rds = boto3.client('rds')

retention_time_days = int(os.environ['SNAPSHOT_RETENTION_DAYS'])

def delete_rds_snapshots(event, context):

    now = datetime.datetime.now().replace(tzinfo=pytz.utc)
    subtract_days = datetime.timedelta(days=retention_time_days)
    #snapshot_cutoff_date = now - subtract_days

    # For testing...
    one_hour = datetime.timedelta(hours=1)
    snapshot_cutoff_date = now - one_hour

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
        snap_id = snapshot['DBSnapshotIdentifier']
        snap_status = snapshot['Status']

        if '-lifecycle-snapshot-' in snap_id and \
            snap_status == 'Available':
            if snap_timestamp < snapshot_cutoff_date:
                try:
                    response = rds.delete_db_snapshot(DBSnapshotIdentifier=snap_id)
                    print "NOTICE: Deleted snapshot '%s'" % snap_id
                except Exception, err:
                    print "ERROR: Could not delete DB snapshot %s: %s" % (snap_id, err)


