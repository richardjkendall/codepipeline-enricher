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


if __name__ == "__main__":
  record = {
    "Message": "{\"account\":\"231965782596\",\"detailType\":\"CodePipeline Pipeline Execution State Change\",\"region\":\"ap-southeast-2\",\"source\":\"aws.codepipeline\",\"time\":\"2020-04-16T22:16:39Z\",\"notificationRuleArn\":\"arn:aws:codestar-notifications:ap-southeast-2:231965782596:notificationrule/e1984e5400185fb3b64f151c60a0428becf5e29b\",\"detail\":{\"pipeline\":\"basic-cicd-pipeline-www-rjk-com-develop-rjk-ecs-dev-www-rjk-com-dev\",\"execution-id\":\"ed501676-0655-4165-9ae7-7f9b0914380a\",\"state\":\"STARTED\",\"version\":1.0},\"resources\":[\"arn:aws:codepipeline:ap-southeast-2:231965782596:basic-cicd-pipeline-www-rjk-com-develop-rjk-ecs-dev-www-rjk-com-dev\"],\"additionalAttributes\":{}}"
  }
  process_record(record)