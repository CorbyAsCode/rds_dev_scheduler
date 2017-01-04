
import boto3

rds = boto3.client('rds')

# Initialize variables as empty strings
event_source = current_db_snapshot_id = event_message = old_snapshot = db_instance_name = ''

def delete_rds_snapshots(event, context):
    # Get the message body
    message = event['Records'][0]['Sns']['Message']

    # Loop through message body and set our variables
    for line in str(message).split(','):
        if 'Event Source' in line:
            event_source = line.split(':')[1].strip('"')
        elif 'Source ID' in line:
            current_db_snapshot_id = line.split(':')[1].strip('"')
        elif 'Event Message' in line:
            event_message = line.split(':')[1].strip('}').strip('"')

    print "Event Source: %s; Source ID: %s; Event Message: %s" % (event_source, current_db_snapshot_id, event_message)

    # Check if the SNS notification we received is the one we need to use
    if event_source == 'db-snapshot' and \
       '-lifecycle-snapshot-' in current_db_snapshot_id and \
       event_message == '':
           print "NOTICE:  This is the notification we're looking for...continuing."
    else:
        print "NOTICE:  This is not the notification we're looking for...exiting."
        return 

    # Need to query our current snapshot to get the DB instance identifier
    try:
        current_snapshot_metadata = rds.describe_db_snapshots(DBSnapshotIdentifier=current_db_snapshot_id)
    except Exception, err:
        print "ERROR: Could not retrieve current snapshot metadata for %s: %s" % (current_db_snapshot_id, err)
        
    # Set the variable using the current snapshot metadata
    db_instance_identifier = current_snapshot_metadata['DBSnapshots'][0]['DBInstanceIdentifier']
    
    # Query for all of the DB instance's snapshots
    try:
        snapshots = rds.describe_db_snapshots(DBInstanceIdentifier=db_instance_identifier)
    except Exception, err:
        print "ERROR: Could not retrieve snapshot metadata for %s: %s" % (db_instance_identifier, err)
    
    # If no other snapshots are found, we can stop here
    if len(snapshots['DBSnapshots']) == 0:
        return
    
    # Loop through all snapshots to see which ones need deleted
    for snapshot in snapshots['DBSnapshots']:
        if snapshot['DBSnapshotIdentifier'] != current_db_snapshot_id:
            if db_instance_identifier in snapshot['DBSnapshotIdentifier']:
                old_snapshot = snapshot['DBSnapshotIdentifier']
                try:
                    response = rds.delete_db_snapshot(DBSnapshotIdentifier=old_snapshot)
                except Exception, err:
                    print "ERROR: Could not delete DB snapshot %s: %s" % (old_snapshot, err)

    