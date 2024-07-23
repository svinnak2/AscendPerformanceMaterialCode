
# %pip install -U PyPDF2
# %pip install langchain==0.0.342 --force-reinstall --quiet


# # restart kernel
# from IPython.core.display import HTML
# HTML("<script>Jupyter.notebook.kernel.restart()</script>")


# Importing the boto3 library for interacting with AWS services
import boto3

# Import os module for interacting with the operating system
import os

# Importing the PyPDF2 library for reading PDF files
import PyPDF2

from langchain.prompts import ChatPromptTemplate

import json

# Import pandas as pd for data manipulation and analysis
import pandas as pd

import time
from TimeMethods import get_Date, get_DateTime, Time

from botocore.config import Config

import argparse


def main():
    parser = argparse.ArgumentParser(description="Process an Number of Searchs and Search Term")
    parser.add_argument("ip_var1", type=str, help="A string input representing Search Term")
    parser.add_argument("ip_var2", type=str, help="A string input representing Material received to classify")

    args = parser.parse_args()

    # Execute the function with the input parameters
    # NUM_RESULTS, MY_SEARCH = process_input(args.number, args.string)

    MY_SEARCH = args.ip_var1
    matrl = args.ip_var2

    return MY_SEARCH, matrl


if __name__ == "__main__":
    MY_SEARCH, matrl = main()

print(f"Search Term: {MY_SEARCH}")
print(f"Number of Results to Query: {matrl}")


# Initialize the Bedrock client
boto3_session = boto3.session.Session()
region_name = boto3_session.region_name

config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    },
    read_timeout=120  # Increase the read timeout as needed
)


client = boto3.client(service_name='bedrock-runtime', region_name=region_name, config=config)  # Use your AWS region
model_Id = 'anthropic.claude-v2:1'
MX_TKN = 4000
TMPRT = 0.1
TOP_P = 0.3
TOP_K = 1
matrl = "nylon6,6"
# matrl = "nylon6,6” or “nylon66” or “nylon 66” or “nylon6.6"



# Get the working directory
wrk_dir = '/home/ec2-user/SageMaker/AscendNotebook'
scraped_data_dir = '/home/ec2-user/SageMaker/AscendNotebook/WebScrapedData'
os.chdir(wrk_dir)
# The directory to save results
Rslts_Save_Dir = wrk_dir + "/CodeExecutionMetrics/"
Sales_Lead_Dir = wrk_dir + "/SalesLeadData/"

print("Present working directory:", wrk_dir)
print("Directory to save results:", Rslts_Save_Dir)
print("Directory to save Sales Leads:", Sales_Lead_Dir)


# # Chose the appropriate search term


# MY_SEARCH = "Nylon & Polyamide injection molders"
# matrl = "Nylon 6"
# MY_SEARCH = "Plastic Profile Extruders"
# MY_SEARCH = "Plastic Sheet extruders"
# MY_SEARCH = "Recycled carpet fibers applications"
# MY_SEARCH = "Nylon Compounders & Polyamide Compounders"


# MY_SEARCHES = ["Nylon & Polyamide injection molders", "Plastic Profile Extruders", "Plastic Sheet extruders", "Recycled carpet fibers applications", "Nylon Compounders & Polyamide Compounders"]


# Function to map a search term to a specific directory name
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
    else:
        raise ValueError(f"Undefined search term: {MY_SEARCH}")


# Define the prompt template
def PROMPT_TEMPLATE(matrl, unstructured_text):
    
    prompt = f"""
        \n\nHuman: You are a sales lead specialist at a leading global manufacturer of high-performance materials, specializing in chemicals, fibers, and plastics, and you are very good at identifying injection molding companies that might purchase material provided in the material tag based on the context provided in the context tag. 

        If you identify a company as an injection molding company that might purchase given material then output saying "Likely to purchase". Additionally, give the reason why you think the company will purchase the material.
        If you are unsure or there is not enough data in the context tag or required responses couldn't be answered, then respond back saying "Not likely to purchase" for Prediction and give your reason why you think the company will not purchase given material and "N/A" for other response fields.
        
        The output should strictly be in JSON format only:

        1. Company_Name: The full name of the company  or "N/A" if there is no data.
        2. Company Website: Provide Company Website or "N/A" if there is no data.
        3. Phone Number: Provide company phone number or "N/A" if there is no data.
        4. Location: Provide company state, country details or "N/A" if there is no data.
        5. Prediction: Predict "Likely to purchase" or "Not likely to purchase".
        6. Prediction_Reason: Give logical, and emotional reasons for your prediction or "N/A" if there is no data.
        
        <material>
        {matrl}
        </material>
        
        <context>
        {unstructured_text}
        </context>

        **Extracted Information (in JSON format):**
        \n\nAssistant:
        """
    return prompt


# Make the API request to AWS Bedrock
def llm_ner_response(model_Id, prompt_cntxt_text, MX_TKN, TMPRT, TOP_K):
    
    response = client.invoke_model(
        modelId = model_Id,  # Model ID for Claude
        contentType = 'application/json',
        accept = 'application/json',
        body = json.dumps({"prompt": prompt_cntxt_text,
                           "max_tokens_to_sample": MX_TKN,
                           "temperature": TMPRT,
                           "top_k": TOP_K,
                          })  # Adjust max_tokens as needed
    )
    
    return response


def is_json(data):
    try:
        json.loads(data)
        return True
    except ValueError:
        return False



def prompt_llm_ner_chain(matrl, unstrct_text, model_Id, MX_TKN, TMPRT, TOP_K):
    prompt_context_text = PROMPT_TEMPLATE(matrl, unstrct_text)
    llm_ner_resp_op = llm_ner_response(model_Id, prompt_context_text, MX_TKN, TMPRT, TOP_K)
    
    response_body = json.loads(llm_ner_resp_op.get('body').read())
    # NER text
   
    json_text = response_body.get('completion')
    
    print(" ")
    print(json_text)

    if is_json(json_text):
        print("The data is in JSON format.")
        print("Printing data Text:")
        data = json.loads(json_text)
        print(data)
        company_name = data.get("Company_Name")
        company_website = data.get("Company Website")
        Phone_Number = data.get("Phone Number")
        Location = data.get("Location")
        Prediction = data.get("Prediction")
        Prediction_Rsn = data.get("Prediction_Reason")
#         Typical_Products_Manufactured = data.get("Products_Typically_Manufactured")
    else:
        print("The data is not in JSON format.")
        print("Printing data Text:")
        print(json_text)
        NJ_data = json_text.rstrip('`')
        NJ_data = NJ_data.lstrip('`')
        NJ_data = NJ_data.strip('`')
        print("Printing data after removing backticks:")
        print(NJ_data)
#         # Extract the JSON part from the text
        start = json_text.find('{')
        end = json_text.find('}') + 1
        ext_data = json_text[start:end]
        print("Extracted JSON Part")
        print(ext_data)
        # Parse the JSON data
#         NJ_data = json.loads(json_text)

        # using json.loads()
        # convert dictionary string to dictionary
        ext_data = json.loads(ext_data)
        
        print("Data Type after extracting data:", type(ext_data))

        # Extract the required fields
        company_name = ext_data["Company_Name"]
        company_website = ext_data["Company Website"]
        Phone_Number = ext_data["Phone Number"]
        Location = ext_data["Location"]
        Prediction = ext_data["Prediction"]
        Prediction_Rsn = ext_data["Prediction_Reason"]
#         Typical_Products_Manufactured = ext_data["Products_Typically_Manufactured"]
    
    return company_name, company_website, Phone_Number, Location, Prediction, Prediction_Rsn



def get_directory_list(matrl, files, model_Id, MX_TKN, TMPRT, TOP_K):
    # The following code reads each file from the directory for NER
    Files_Processed = 0
    JSON_RESP_Final = pd.DataFrame(columns = ['FileName', 'Company Name', 'company_website', 'Phone_Number', 'Location', 'Predicted_Value', 'Prediction_Reason', 'Typical_Products_Manufactured'])

    for file in files:
        print("Reading File:", Files_Processed)
        print("Reading file name:", file)

        if ".txt" in file:
            with open(file, 'r') as file:
                unstructured_text = file.read()
    #             print(unstructured_text)
                company_name, company_website, Phone_Number, Location, Prediction, Prediction_Rsn = prompt_llm_ner_chain(matrl, unstructured_text, model_Id, MX_TKN, TMPRT, TOP_K)
        elif ".pdf" in file:
            with open(file, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                unstructured_text = ""
                for page in reader.pages:
                    unstructured_text += page.extract_text()
    #         print(unstructured_text)
                company_name, company_website, Phone_Number, Location, Prediction, Prediction_Rsn = prompt_llm_ner_chain(matrl, unstructured_text, model_Id, MX_TKN, TMPRT, TOP_K)

        # Define a new row as a dictionary
        new_row = {'FileName': file,'Company Name': company_name, 'company_website': company_website,
                   'Phone_Number': Phone_Number, 'Location': Location, 'Predicted_Value': Prediction, 
                   'Prediction_Reason': Prediction_Rsn}
        # Append the row
        JSON_RESP_Final.loc[len(JSON_RESP_Final)] = new_row

        Files_Processed+=1
        print(" ")

    os.chdir(wrk_dir)
    
    return JSON_RESP_Final, Files_Processed



# Start scraping from the homepage

NER_processing_time = pd.DataFrame(columns = ['Search Term','Files Processed', 'Start Time', 'End Time', 'Execution_Time'])

start_time = time.time()
# Print the formatted date and time
print(f"Starting NER job for {MY_SEARCH} at: {get_DateTime()}")

# Get the directory name to process files
SEARCH_TERM_DIR = search_term_directory(MY_SEARCH)
print("Files Search Directory to Work:", SEARCH_TERM_DIR)

current_directory = os.getcwd()
print("Current working directory:", current_directory)

# Change directory to the folder containing files
os.chdir(f"{scraped_data_dir}/{SEARCH_TERM_DIR}")
print()

current_directory = os.getcwd()
print("Current working directory:", current_directory)

files = [f for f in os.listdir(current_directory) if os.path.isfile(os.path.join(current_directory, f))]

print(files)

JSON_RESP_Final, Files_Processed = get_directory_list(matrl, files, model_Id, MX_TKN, TMPRT, TOP_K)

end_time = time.time()
execution_time = (end_time - start_time)/60  # Calculate the execution time

# Define a new row as a dictionary
ner_proc_tm_new_row = {'Search Term': MY_SEARCH, 'Files Processed': Files_Processed, 
                       'Start Time': start_time, 'End Time': end_time, 'Execution_Time': execution_time}

# Append the row
NER_processing_time.loc[len(NER_processing_time)] = ner_proc_tm_new_row


# JSON_RESP_Final.to_csv(Rslts_Save_Dir + "/" + SEARCH_TERM_DIR + "_NER_Classify_"+ get_DateTime() + '.csv', index=False)
NER_processing_time.to_csv(Rslts_Save_Dir + "/" + SEARCH_TERM_DIR + "_NER_Classify_Proc_Tm_"+ get_DateTime() + '.csv', index=False)

# Create Sales Lead of customers that are "Likely to purchase" with select columns of interest only
DF_Col_OF_INT = JSON_RESP_Final[['Company Name', 'company_website','Phone_Number', 'Location', 'Predicted_Value', 'Prediction_Reason']]
DF_Col_OF_INT.fillna('N/A', inplace=False)
Sales_Leads = DF_Col_OF_INT[DF_Col_OF_INT['Predicted_Value'] == 'Likely to purchase']
Sales_Leads.to_csv(Sales_Lead_Dir + "/" + SEARCH_TERM_DIR + "_NER_Classify_"+ '.csv', index=False)

os.chdir(wrk_dir)
print("Current working directory:", wrk_dir)
print("================================")
print(" ")