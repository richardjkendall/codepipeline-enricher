import boto3
import json
import os
import traceback

cp = boto3.client("codepipeline", region_name=os.environ["region"])
sqs = boto3.resource("sqs", region_name=os.environ["region"])

def get_pipeline_execution(pipeline_name, exec_id):
  pipeline_exec = cp.get_pipeline_execution(
    pipelineName=pipeline_name,
    pipelineExecutionId=exec_id
  )
  sha = pipeline_exec["pipelineExecution"]["artifactRevisions"][0]["revisionId"]
  return {
    "sha": sha
  }

def get_pipeline_details(pipeline_name):
  owner = ""
  repo = ""
  branch = ""
  pipeline = cp.get_pipeline(name=pipeline_name)
  stages = pipeline["pipeline"]["stages"]
  for stage in stages:
    if stage["name"] == "Source":
      action = stage["actions"][0]
      owner = action["configuration"]["Owner"]
      repo = action["configuration"]["Repo"]
      branch = action["configuration"]["Branch"]
  return {
    "owner": owner,
    "repo": repo,
    "branch": branch
  }    

def process_record(record):
  print(record)
  msg = json.loads(record)
  msg = json.loads(msg["Message"])
  pipeline_name = msg["detail"]["pipeline"]
  exec_id = msg["detail"]["execution-id"]
  state = msg["detail"]["state"]
  pipeline_details = get_pipeline_details(pipeline_name)
  exec_details = get_pipeline_execution(
    pipeline_name=pipeline_name,
    exec_id=exec_id
  )
  pipeline_details.update(exec_details)
  enriched = {
    "pipeline_name": pipeline_name,
    "exec_id": exec_id,
    "state": state,
    "github": pipeline_details
  }
  print(enriched)
  queue = sqs.get_queue_by_name(QueueName=os.environ["queue"])
  queue.send_message(
    MessageBody=json.dumps(enriched)
  )

def entry(event, context):
  for record in event["Records"]:
    try:
      process_record(record["body"])
    except Exception as err:
      print("Had an error, skipping...")
      traceback.print_tb(err.__traceback__)
      pass
