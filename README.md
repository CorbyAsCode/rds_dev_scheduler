# rds_dev_scheduler
AWS RDS development instance automation

These scripts and configurations are an attempt at automating the scheduled spin-up and shutdown of Development RDS instances.
Use of these scripts will allow you to schedule RDS instance deletion whenever you're not expecting your developers to be using 
the databases, thereby, saving you lots of $$$.

## High-Level Process

1. Modify DB instances and provide the required tag.  Also, disable automatic backups because this process will create a final snapshot prior to deleting an instance.
2. Create an SNS topic. 
3. Set up Lambda functions with correct variables and values. Subscribe the 'modify_rds_instance.py' script to your SNS topic.
4. Create an RDS Event Subscription for Instance Restoration and subscribe it to your SNS topic.
5. Create CloudWatch Events schedules to execute the Lambda functions for 'create_rds_instances.py', 'delete_rds_instances.py', and 'delete_rds_snapshots.py'.
