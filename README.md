# codepipeline-enricher
Lambda function which enriches codepipeline notifications with additional data

## How it works
Picks up AWS CodeStar notifications from an SQS queue and enriches them with additional details.  It is designed to work with the following types of notification:

* codepipeline-pipeline-pipeline-execution-failed
* codepipeline-pipeline-pipeline-execution-canceled
* codepipeline-pipeline-pipeline-execution-started
* codepipeline-pipeline-pipeline-execution-resumed
* codepipeline-pipeline-pipeline-execution-succeeded
* codepipeline-pipeline-pipeline-execution-superseded

You can find more details on these notifications here: https://docs.aws.amazon.com/codestar-notifications/latest/userguide/concepts.html#concepts-api

## What enrichment is done
The code collects details about the source which triggered the pipeline to run.  It expects it to be a Github repository and adds those details to the message before posting it to another SQS queue.

## How to set-up
You will need to create an SQS queue and subscribe it to the SNS topic to which codepipeline is sending notifications.  This lambda function should be triggered by that queue.
the lambda function needs two environment variables:

* ``region``: the region in which it is running
* ``queue``: the name of the SQS queue where the enriched message should be placed.

### Note:
You may want to set a delivery delay on the SQS queue with the codepipeline notifications on it as I've found that the get-pipeline-execution API call does not always work when called very soon after an execution has begun - it is eventually consistent.  I use a delay of 10 seconds.

## Deploying
There is a terraform module which deploys this along with all the other bits and pieces it needs to work.  You can find it here: https://github.com/richardjkendall/tf-modules/tree/master/modules/github-status-updater
