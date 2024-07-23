#!/usr/bin/env python
# coding: utf-8

# In[1]:


import boto3
import os
import time
from TimeMethods import get_Date, get_DateTime, Time
import pandas as pd
from io import StringIO


# In[2]:


boto3_session = boto3.session.Session()
region_name = boto3_session.region_name
s3_client = boto3.client("s3")

# The Source Directory containing the individual sales generation lead files
Sales_Lead_Dir = "/home/ec2-user/SageMaker/AscendNotebook/SalesLeadData/"

# Target S3 bucket name (Replace with appropriate bucket name)
bucket_name = "webpages-bucket-22d2c932-c87e-4ee0-9a93-7f5704931b82"

# Folder name in the bucket
folder_nm_in_bucket = "Sales_Leads_Directory"
filename = "CombinedSalesLeads.csv"

# Get the working directory
wrk_dir = os.getcwd()


# In[3]:


print(f"Source directory from which Sales Generation Leads files are extracted: {Sales_Lead_Dir}")


# In[4]:


# Read file names as a list
files = [f for f in os.listdir(Sales_Lead_Dir) if os.path.isfile(os.path.join(Sales_Lead_Dir, f))]


# In[5]:


#Read each file and combine them to create a dataframe
combined_csv = pd.concat([pd.read_csv(Sales_Lead_Dir + f) for f in files ])

# Prepare the file to be uploaded to S3 and convert the dataframe to a CSV file
csv_buffer = StringIO()
combined_csv.to_csv(csv_buffer, index=False)

# Generate the full path where the file will be uploaded
full_path = f"{folder_nm_in_bucket}/{filename}" if folder_nm_in_bucket else filename

# Upload the CSV file to S3
s3_client.put_object(Bucket=bucket_name, Key=full_path, Body=csv_buffer.getvalue())


# In[ ]:

print(f"Finished placing Sales Generation Lead directory file \"{filename}\" in {bucket_name}/{folder_nm_in_bucket}")


