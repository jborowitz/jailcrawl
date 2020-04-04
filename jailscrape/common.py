from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import selenium as sm
import boto3
import boto.s3
from datetime import datetime 

def parse_configs(config_file):
    config = {line.split('=')[0]:line.split('=')[1].strip() for line in open(config_file).readlines()}
    return config
configs = parse_configs('/opt/jailscrape/conf.env')
BUCKET = configs['BUCKET']
KEY_ID = configs['AWS_KEY']
ACCESS_KEY = configs['AWS_SECRET']
def save_to_s3(page_data, page_number_within_scrape, roster_row):

    county = roster_row['County']
    state = roster_row['State']
    s3 = boto3.resource(
        's3',
        region_name='us-east-1',
        aws_access_key_id=KEY_ID,
        aws_secret_access_key=ACCESS_KEY
    )

    date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_page_{}.html'.format(page_number_within_scrape)
    print(filename)
    s3.Object(BUCKET,filename).put(Body=page_data)

def get_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    browser = webdriver.Chrome(options=chrome_options)
    return browser
