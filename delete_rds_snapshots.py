
import boto3

# May have to modify the SNS message parts since it will be coming from RDS instead of CF

rds = boto3.client('rds')
logical_resource_ids = ('Snapshot-PostgresDB', 'Snapshot-OracleDB')
# Initialize variables as empty strings
resource_type = resource_status = old_snapshot = db_instance_name = logical_resource_id = \
        current_DBSnapshotIdentifier = stack_name = ''

def delete_rds_snapshots(event, context):
    # Get the message body
    message = event['Records'][0]['Sns']['Message']

    # Loop through message body and set our variables
    for line in str(message).split('\n'):
        if line.startswith('ResourceType='):
            resource_type = line.split('=')[1].strip("'")
        elif line.startswith('ResourceStatus='):
            resource_status = line.split('=')[1].strip("'")
        elif line.startswith('LogicalResourceId='):
            logical_resource_id = line.split('=')[1].strip("'")
        elif line.startswith('PhysicalResourceId='):
            current_DBSnapshotIdentifier = line.split('=')[1].strip("'")
        elif line.startswith('StackName='):
            stack_name = line.split('=')[1].strip("'")
            
    # Check if the SNS notification we received is the one we need to use
    if resource_type == 'AWS::RDS::DBSnapshot' and \
       resource_status == 'CREATE_COMPLETE' and \
       logical_resource_id in logical_resource_ids:
           print "NOTICE:  This is the notification we're looking for...continuing."
    else:
        print "NOTICE:  This is not the notification we're looking for...exiting."
        return 

    # Need to query our current snapshot to get the DB instance identifier
    try:
        current_snapshot_metadata = rds.describe_db_snapshots(DBSnapshotIdentifier=current_DBSnapshotIdentifier)
    except Exception, err:
        print "ERROR: Could not retrieve current snapshot metadata for %s: %s" % (current_DBSnapshotIdentifier, err)
        
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
        if snapshot['DBSnapshotIdentifier'] != current_DBSnapshotIdentifier:
            if stack_name in snapshot['DBSnapshotIdentifier']:
                old_snapshot = snapshot['DBSnapshotIdentifier']
                try:
                    response = rds.delete_db_snapshot(DBSnapshotIdentifier=old_snapshot)
                except Exception, err:
                    print "ERROR: Could not delete DB snapshot %s: %s" % (old_snapshot, err)

    