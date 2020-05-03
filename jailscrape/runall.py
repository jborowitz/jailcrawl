import glob
import ipdb
import subprocess
import math
import logging
import watchtower
import uuid
import pandas
import boto3
import datetime

runname = str(uuid.uuid4())[0:8]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__ + '_' + runname)
logger.addHandler(watchtower.CloudWatchLogHandler())
configs = {line.split('=')[0]:line.split('=')[1].strip() for line in open('/opt/jailscrape/conf.env').readlines()}
BUCKET = configs['BUCKET']

scripts_to_run =glob.glob('*.py') 
logger.info('There are %s scripts to run', len(scripts_to_run))
num_simultaneous_scripts = 20
results_list = []
#for n in [0,1]:
for n in range(math.ceil(len(scripts_to_run) / num_simultaneous_scripts )):
    process_dict = {}
    for script in scripts_to_run[(n*num_simultaneous_scripts):((n+1)*num_simultaneous_scripts)]:
        process = subprocess.Popen(['python', script], stdout=subprocess.PIPE)
        process_dict[script] = process
        logger.info('added script %s', process)
    for script, process in process_dict.items():
        result = {}
        result['script'] = script
        logger.info('communicating for script _%s_', script)
        result['timeout'] = False
        try:
            stdout = process.communicate(timeout=600)[0]
        except subprocess.TimeoutExpired:
            logger.info('Process _%s_ timed out', script)
            result['timeout'] = True
        code = process.wait()
        result['exit_code'] = code
        results_list.append(result)
        print(stdout, code)

s3 = boto3.resource( # Do not specificy keys for boto3. What's happening here is 
    's3',
    region_name='us-east-1',
)
df = pandas.DataFrame(results_list)
newdf = pandas.DataFrame({'script':scripts_to_run})
df = newdf.merge(df, how='left')
df['attempted'] = df['exit_code'].notnull()

s3.Object(BUCKET,'daily_run_summaries/%s-run_%s_exit_code_summary.csv' % (datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d'),runname)).put(Body=df.to_csv())
