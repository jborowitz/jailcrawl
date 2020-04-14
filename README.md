# Docker

The Jailcrawl runs in a docker container. To run this, you first need to install [docker](https://www.docker.com/). Then, follow the steps below:

 1. Create a file `conf.env` in your project root directory. Define 2 variables like:
 ```
BUCKET=jailcrawlsample
FAILURE_SNS_TOPIC=arn:aws:sns:us-east-1:153598194566:jailcrawl_errors
 ```
 The `BUCKET` variable denotes the Amazon s3 bucket where the documents will be stored. The `FAILURE_SNS_TOPIC` variable is the Amazon Simple Notification Service "Topic" where error messages will be emailed.
 
 2. In a file called `credentials` in your project root, put the following, using your AWS credentials:
```
[default]
aws_access_key_id=AKXXXXX
aws_secret_access_key=dxsQXXXXXX
```
 3. Build the docker container:
```
docker build -t jailcrawl .
```
 4. Run the container. There are two modes to run. To run a single file, do `run_one` with a pointer to the specific file you'd like to run:
 ```
docker run -i -t  test run_one ./Arkansas_marion.py
 ```
To run all files, do:
```
docker run -i -t  test run_all
 ```
# Code format

Common files and functions are in `jailcrawl/common.py`. These include utilities for saving to S3, logging to AWS CloudWatch and persisting errors.


## Working Scrapers

All working scrapers in the project directory `./working_scrapers/` are deployed and will be run. For instance, you can run a scraper at `./working_scrapers/Arkansas_greene.py` by running `docker run -i -t  test run_one ./Arkansas_marion.py`. Scrapers that are not working are in the `./to_fix/` directory.

