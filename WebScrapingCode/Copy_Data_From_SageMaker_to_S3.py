#!/usr/bin/env python
# coding: utf-8

# In[1]:


import boto3
import os
import time
from TimeMethods import get_Date, get_DateTime, Time
import pandas as pd


# In[2]:


boto3_session = boto3.session.Session()
region_name = boto3_session.region_name
s3_client = boto3.client("s3")

# Source Sage Maker Directory containing the Web scrapped data that needs to be copied to S3 Directory
SG_MKR_Directory = "/home/ec2-user/SageMaker/AscendNB/WebScrapedUpdatedApproach"

# Target S3 bucket name (Replace with appropriate bucket name)
bucket_name = "webpages-bucket-22d2c932-c87e-4ee0-9a93-7f5704931b82"

# Initialize Tgt Folder Name
Tgt_folder_nm = "WebScraped_Data/" 

# Get the working directory
wrk_dir = os.getcwd()

# The directory to save results
Rslts_Save_Dir = "/home/ec2-user/SageMaker/AscendNotebook/CodeExecutionMetrics/"


# In[3]:


# MY_SEARCH = "Nylon & Polyamide injection molders"
# MY_SEARCH = "Plastic Profile Extruders"
# MY_SEARCH = "Plastic Sheet extruders"
# MY_SEARCH = "Recycled carpet fibers applications"

MY_SEARCHES = ["Nylon & Polyamide injection molders", "Plastic Profile Extruders", "Plastic Sheet extruders", "Recycled carpet fibers applications", "Nylon Compounders & Polyamide Compounders", "Revised Search Terms"]


# In[4]:


def search_term_directory(MY_SEARCH):
    if MY_SEARCH == "Nylon & Polyamide injection molders":
        return "Nylon_Polyamide_injection_molders"
    elif MY_SEARCH == "Plastic Profile Extruders":
        return "Plastic_Profile_Extruders"
    elif MY_SEARCH == "Plastic Sheet extruders":
        return "Plastic_Sheet_Extruders"
    elif MY_SEARCH == "Recycled carpet fibers applications":
        return "Recycled_carpet_fibers_applications"
    elif MY_SEARCH == "Nylon Compounders & Polyamide Compounders":
        return "Nylon_Compounders_Polyamide_Compounders"
    elif MY_SEARCH == "Revised Search Terms":
        return "Revised_Search_Terms"
    else:
        raise ValueError(f"Undefined search term: {MY_SEARCH}")


# In[5]:


# Upload data to s3
def uploadDirectory(path, bucket_name, s3_prefix):
    for root, dirs, files in os.walk(path):
        for file in files:
            s3_key = s3_prefix + file
#             print("File Name:", file)
#             print(s3_key)
#             print(" ")
            s3_client.upload_file(os.path.join(root,file), bucket_name, s3_key)


# In[6]:


def DataCopy_to_S3 (SEARCH_TERM_DIR, Source_Directory, bucket_name, s3_prefix):
    path = Source_Directory + "/" + SEARCH_TERM_DIR + "/"
    print ("s3 Path:", s3_prefix)
    uploadDirectory(path, bucket_name, s3_prefix)


# In[7]:


# Start scraping from the homepage

CopyData_to_S3_processing_time = pd.DataFrame(columns = ['Search Term','Copy Start Time', 'Copy End Time'])

for MY_SEARCH in MY_SEARCHES:
    start_time = time.time()
    # Print the formatted date and time
    print(f"Starting Copying job {MY_SEARCH} at: {get_DateTime()}")
    
    # Define search term directory to save web scrapping results
    SEARCH_TERM_DIR = search_term_directory(MY_SEARCH)

    DataCopy_to_S3(SEARCH_TERM_DIR, SG_MKR_Directory, bucket_name, Tgt_folder_nm)

    end_time = time.time()
    execution_time = (end_time - start_time)/60  # Calculate the execution time

    print(f"It took {execution_time} minutes to copy the data from SageMaker to S3")

    # Define a new row as a dictionary
    copy_new_row = {'Search Term': MY_SEARCH, 'Copy Start Time': start_time, 'Copy End Time': end_time}
    
    # Append the row
    CopyData_to_S3_processing_time.loc[len(CopyData_to_S3_processing_time)] = copy_new_row
    
CopyData_to_S3_processing_time.to_csv(Rslts_Save_Dir + "/" +"CopyData_to_S3_Processing_Time"+ get_DateTime() + '.csv', index=False)


# In[ ]:




