from selenium.webdriver.common.keys import Keys
import json
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import selenium as sm
import boto3
import boto.s3
from datetime import datetime 
import watchtower
import logging


def get_logger(roster_row):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('%s_%s' % (roster_row['State'],roster_row['County']))
    logger.addHandler(watchtower.CloudWatchLogHandler())
    return logger
def parse_configs(config_file):
    config = {line.split('=')[0]:line.split('=')[1].strip() for line in open(config_file).readlines()}
    return config
configs = parse_configs('/opt/jailscrape/conf.env')
BUCKET = configs['BUCKET']
FAILURE_SNS_TOPIC = configs['FAILURE_SNS_TOPIC']
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())
logger.info('Set BUCKET to _%s',BUCKET)
s3 = boto3.resource(
    's3',
    region_name='us-east-1',
    #aws_access_key_id=KEY_ID,
    #aws_secret_access_key=ACCESS_KEY
)

def save_to_s3(page_data, page_number_within_scrape, roster_row):
    county = roster_row['County']
    state = roster_row['State']

    date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_page_{}.html'.format(page_number_within_scrape)
    print(filename)
    logger.info('Saved file: _%s_', filename)
    s3.Object(BUCKET,filename).put(Body=page_data)

def record_error(message, page_number_within_scrape, roster_row):
    county = roster_row['County']
    state = roster_row['State']
    date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = 'Errors/' + state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_page_{}.html'.format(page_number_within_scrape)
    print('Error on file: _%s_' % filename)
    logger.error('Error on file: _%s_', filename)
    s3.Object(BUCKET,filename).put(Body=message)
    message = {
            "County": county,
            "State": state,
            }
    sns = boto3.client('sns')
    response = sns.publish(
                TargetArn=FAILURE_SNS_TOPIC,
                Message=json.dumps(message)
    )

def get_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    browser = webdriver.Chrome(options=chrome_options)
    return browser
