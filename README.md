# rds_dev_scheduler
AWS RDS development instance automation

*This code is actually obsolete due to the fact that AWS now provides an API to shutdown/startup an RDS instance.*

These scripts and configurations are an attempt at automating the scheduled spin-up and shutdown of Development RDS instances.
Use of these scripts will allow you to schedule RDS instance deletion whenever you're not expecting your developers to be using 
the databases, thereby, saving you lots of $$$.

## High-Level Process

1. Modify DB instances and provide the required tag.  Also, disable automatic backups because this process will create a final snapshot prior to deleting an instance.
2. Create an SNS topic for 'modify_rds_instance.py'. 
3. Set up Lambda functions with correct variables and values. Subscribe the 'modify_rds_instance.py' script to your SNS topic.
4. Create an RDS Event Subscription for Instance Restoration and subscribe it to your SNS topic.
5. Create CloudWatch Events schedules to execute the Lambda functions for 'create_rds_instances.py', 'delete_rds_instances.py', and 'delete_rds_snapshots.py'.


## Behind the Scenes
Each Lambda function is configurable via environment variables.

### create_rds_instances.py
Creates RDS instances using metadata stored in S3 by the delete_rds_instances.py script.

#### Variables
- WEEK_TO_EXECUTE - values (all|first|last|[0-6])
  - Specifies a more granular weekly schedule within a month
  - all: execute every week of the month
  - first: execute on the first full week of the month
  - last: execute on the last full week of the month
  - [0-6]: execute on a specific full week of the month
  
- APP_LIFECYCLE_TAG - values (string)
  - Used to mark instances to be managed by this process
  
- S3_BUCKET_NAME - values (string)
  - The name of the S3 bucket where you're going to store the DB metadata
  
- S3_DIR_NAME - values (string)
  - The name of the S3 directory where you're going to store the DB metadata
  
- RDS_METADATA_FILENAME - values (string)
  - The name of the S3 object store where your DB metadata will be saved prior to deletion
  
### delete_rds_instances.py
Deletes RDS instances that are tagged with "AppLifecycle: $APP_LIFECYCLE_TAG".  Creates a final snapshot and saves the DB instances' metadata in S3.

#### Variables
- APP_LIFECYCLE_TAG - values (string)
  - The tag to search for in RDS
  
- S3_BUCKET_NAME - values (string)
  - The name of the S3 bucket where you're going to store the DB metadata
  
- S3_DIR_NAME - values (string)
  - The name of the S3 directory where you're going to store the DB metadata
  
- RDS_METADATA_FILENAME - values (string)
  - The name of the S3 object store where your DB metadata will be saved prior to deletion
  
### delete_rds_snapshots.py
Deletes snapshots that are older than $SNAPSHOT_RETENTION_DAYS and contain '-lifecycle-snapshot-' in their name.

#### Variables
- SNAPSHOT_RETENTION_DAYS - values (integer)
  - Age of snapshots in days to retain
  
### modify_rds_instance.py
Modifies an RDS instance after it is created to add it to the correct Subnet Groups.

#### Variables
- S3_BUCKET_NAME - values (string)
  - The name of the S3 bucket where you're going to store the DB metadata
  
- S3_DIR_NAME - values (string)
  - The name of the S3 directory where you're going to store the DB metadata
  
- RDS_METADATA_FILENAME - values (string)
  - The name of the S3 object store where your DB metadata will be saved prior to deletion
  
