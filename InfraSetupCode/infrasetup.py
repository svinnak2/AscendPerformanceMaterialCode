import boto3
import os

def create_folder_in_s3(bucket_name, folder_name):
    s3 = boto3.client('s3')
    folder_key = folder_name if folder_name.endswith('/') else folder_name + '/'

    # Check if the folder already exists
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_key, Delimiter='/')
    if 'Contents' not in response:
        # Folder does not exist, so create it
        s3.put_object(Bucket=bucket_name, Key=folder_key)
        print(f"Folder \"{folder_key}\" is created in bucket \"{bucket_name}\".")
        print("")
    else:
        print(f"Folder \"{folder_name}\" already exists in bucket \"{bucket_name}\".")
        print("")

def create_folder_in_sm(ROOT_DIR, NEW_DIR):
    # Check if the folder already exists
    # Check if the Search Term Directory exists
    if not os.path.exists(f"{ROOT_DIR}/{NEW_DIR}"):
        # Create the directory
        os.makedirs(f"{ROOT_DIR}/{NEW_DIR}")
        print(f"Directory '{NEW_DIR}' created.")
        print(" ")
    else:
        print(f"Directory '{NEW_DIR}' already exists.")
        print(" ")