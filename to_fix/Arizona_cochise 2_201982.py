from urllib.request import urlopen, Request
import pandas as pd
import selenium as sm
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import os
import time
import numpy as np
from datetime import datetime
import datetime as dt
import sys
from io import StringIO
from joblib import Parallel, delayed
import boto3
import boto.s3
import requests

KEY_ID = 'AKIAIIJA7TBYB2EAMHQA'
ACCESS_KEY = 'ZlZqfd4nzTp1ystm99X/XZpbVCe0kE1fAKSUasfk'

s3 = boto3.resource(
    's3',
    region_name='us-east-1',
    aws_access_key_id=KEY_ID,
    aws_secret_access_key=ACCESS_KEY
)


#INSERT PATH TO THE FILE WHERE YOU WILL BE STORING YOUR FILES BELOW (allPrisonersProject)
#root_directory = '/Users/hisamsabouni/Documents/Deangelo_research/allPrisonersProject'
root_directory = '/Users/davidmertenjones/Jupyter_Notebooks/Thinkful_Curriculum/CGU328/jailproject/allPrisonersProject'

os.chdir(root_directory)
from essentials import *

def main(urlAddress):
    try:
        #urlAddress = roster['Working Link'].values[index]
        
        req = requests.get(urlAddress)
        pdf_data = req.content
        
        #Mark the time the file is collected
        date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #Create an html file with the name of the time stamp collected and write the page to a folder 
        #Within the root directory. Replace county and city with the county and city you are working on.
        
        #Toggle local/s3 storage
        aws = True
        
        if aws == True:
            s3.Object('jailcrawl',state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '.pdf').put(Body=pdf_data)
        else:
            if not os.path.exists('./Scrapings/{}/{}/'.format(state, county)):
                os.makedirs('./Scrapings/{}/{}/'.format(state, county))
        
            file_ = open(root_directory + '/Scrapings/{}/{}/'.format(state, county) + date_collected + '.pdf', 'wb')
            file_.write(pdf_data)
            file_.close() #close the writing of the file
        
    except Exception as errorMessage:
        #Post error to firebase server
        date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {'Message':str(errorMessage)}
        firebase.put('/ErrorLogs/'+locationInUse+'/',date_collected,data)
        pass
    
        

if __name__ == "__main__":
    #Will collect the data in parallel to speed up computation
    #num_cores = 12
    #inputs = range(len(all_urls))
    #getCounty = Parallel(n_jobs=num_cores)(delayed(main)(i) for i in tqdm(inputs))
    #This will load in the current jail roster list
    #Select the index of the roster this script is for:
    #Write the name of the county and state
    global roster, locations
    roster = pd.read_csv('jail_roster_final_rmDuplicates.csv',encoding = "utf-8")
    locations = []
    for row in range(roster.shape[0] - 1):
        stp = str(roster['State'].values[row]) +', '+ str(roster['County'].values[row])
        locations.append(bytes(stp, 'utf-8').decode('utf-8', 'ignore').replace('.','').replace('/',''))
    
    global firebase, county, state
    firebase = loginToFirebase()
    index = 23
    locationInUse = locations[index]
    state = roster.State[index]
    county = roster.County[index]
    main(roster['Working Link'].values[index])
