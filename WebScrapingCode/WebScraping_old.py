#!/usr/bin/env python
# coding: utf-8

# In[1]:


# %pip install google-api-python-client
# %pip install -U langchain-community
# %pip install -U langchain-aws
# %pip install -U langfuse


# In[2]:


# restart kernel
# from IPython.core.display import HTML
# HTML("<script>Jupyter.notebook.kernel.restart()</script>")


# In[3]:


# Import the build function from googleapiclient.discovery to create a service object for Google APIs
from googleapiclient.discovery import build

# Import pprint function from pprint module and alias it as pp for pretty-printing of data structures
from pprint import pprint as pp

# Import math module for mathematical functions and constants
import math

# Import urlparse function from urllib.parse module for parsing URLs
from urllib.parse import urljoin, urlparse

# Import pandas as pd for data manipulation and analysis
import pandas as pd

# Import os module for interacting with the operating system
import os

# Import the requests module for making HTTP requests
import requests

# Import BeautifulSoup class from bs4 module for parsing HTML and XML documents
from bs4 import BeautifulSoup

# Import re module for regular expression operations
import re

from TimeMethods import get_Date, get_DateTime, Time


# In[ ]:


# Based on search term this function defines the folder to store scrapped data


# In[6]:


def search_term_directory(MY_SEARCH):
    if "Nylon & Polyamide injection molders" in MY_SEARCH:
        return "Nylon_Polyamide_injection_molders"
    elif "Plastic Profile Extruders" in MY_SEARCH:
        return "Plastic_Profile_Extruders"
    elif "Plastic Sheet extruders" in MY_SEARCH:
        return "Plastic_Sheet_Extruders"
    elif "Recycled carpet fibers applications" in MY_SEARCH:
        return "Recycled_carpet_fibers_applications"
    elif "Nylon Compounders & Polyamide Compounders" in MY_SEARCH:
        return "Nylon_Compounders_Polyamide_Compounders"
    else:
        raise ValueError(f"Undefined search term: {MY_SEARCH}")


# In[8]:


def google_search(search_term, api_key, cse_id, **kwargs):
    """
    Performs a Google Custom Search API query.

    Args:
        search_term (str): The query string to search for.
        api_key (str): The API key for accessing the Google Custom Search API.
        cse_id (str): The Custom Search Engine ID.
        **kwargs: Additional parameters to pass to the search query.

    Returns:
        items_to_return: The search results as a dictionary.
    """
    
    service = build("customsearch", "v1", developerKey=api_key)
    
    num_search_results = kwargs['num']
    print(num_search_results)
    if num_search_results > 500:
        raise NotImplementedError('Google Custom Search API supports max of 500 results')
    elif num_search_results > 100:
        kwargs['num'] = 100 # this cannot be > 10 in API call 
        calls_to_make = math.ceil(num_search_results / 10)
    else:
        calls_to_make = 1
        
    kwargs['start'] = start_item = 1
    items_to_return = []
    while calls_to_make > 0:
        res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
        print(res)
        items_to_return.extend(res['items'])
        calls_to_make -= 1
        start_item += 100
        kwargs['start'] = start_item
        leftover = num_search_results - start_item + 1
        if 0 < leftover < 100:
            kwargs['num'] = leftover
        
    return items_to_return


# In[9]:


def extract_company_name_old(url):
    """
    Extracts and capitalizes the company name from a given URL.

    Args:
        url (str): The URL from which to extract the company name.

    Returns:
        str: The extracted and capitalized company name.
    """
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    company_name = domain.split(".", 2)[1]  # Extract the first part of the domain (company name)
    # print(parsed_url)
    # print(domain)
    # print(company_name)
    return company_name.capitalize()  # Capitalize the company name for consistency


# In[10]:


def extract_company_name(url):
    # Remove protocol (http, https) and 'www'
    cleaned_url = re.sub(r'https?://(www\.)?', '', url)
    # Split by non-alphanumeric characters and take the first part
    company_name = re.split(r'[\W_]', cleaned_url)[0]
    return company_name.capitalize()  # Capitalize the company name for consistency


# In[11]:


def fetch_url_content(url):
    """
    Fetches and cleans the full content from a given URL.

    Args:
        url (str): The URL from which to fetch the content.

    Returns:
        str: The cleaned text content from the URL.
    """
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception if response is not successful
        soup = BeautifulSoup(response.text, "html.parser")
        full_content = soup.get_text()  # Extract full text from the webpage
        # Remove multiple empty lines using regex
        cleaned_text_1 = re.sub(r'\n\s*\n', '\n', full_content)
        cleaned_text = cleaned_text_1.strip()
        return cleaned_text
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# In[12]:


def fetch_pdf_content(url):
    
    try:
        print("The text contains '.pdf'.")
        # Fetch and print the full content of the pdf file
        response = requests.get(url, timeout=30)

        # Extract Pdf file name from URL
        pdf_file_name = os.path.basename(url)
        print("The pdf file name is", pdf_file_name)

        # save pdf file name
        with open(pdf_file_name, "wb") as file:
            file.write(response.content)
        return None
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# In[13]:


def crawl_search_term(MY_SEARCH, TIOT_API_KEY, MY_CSE_ID,NUM_RESULTS):
    
    Crawl_Start_DT_TM = get_DateTime()
    start_time = Time()
    print(f"--> Starting Crawling for {MY_SEARCH} term at: {Crawl_Start_DT_TM}")
    results = google_search(MY_SEARCH, TIOT_API_KEY, MY_CSE_ID, num=NUM_RESULTS)
    Crawl_End_DT_TM = get_DateTime()
    end_time = Time()
    crawl_execution_time = (end_time - start_time)/60  # Calculate the execution time
    
    print(f"--> Finished Crawling for {MY_SEARCH} term at: {Crawl_End_DT_TM}")
    print(" ")
    
    # Define a new row as a dictionary
    Crawl_process_stats = {'Search Term': MY_SEARCH, 'Number of Results Crawled': NUM_RESULTS, 'Crawl Start Time': Crawl_Start_DT_TM,
                     'Crawl End Time': Crawl_End_DT_TM, 'Crawl Exec Time in Minutes': crawl_execution_time}
    
    return Crawl_process_stats, results


# In[14]:


def scrap_websites(RSLTS, MY_SEARCH, ROOT_DIR, SEARCH_TERM_DIR, wrk_dir, Search_Date):
    
    # Print the results
    counter = 0
    Metadata_DF_Final = pd.DataFrame(columns = ['Search Term', 'Title', 'Company URL', 'Company Name', 'Search Date', 
                                               'File Type', 'File Name', 'Download Status'])
    for result in RSLTS:

        # At the begining of the scrapping, check if the directory exist to save files or not
        
        if counter == 0:
            # Print the current working directory to verify the change
            print("--> Current Working Directory:", os.getcwd())

            # Check if the Search Term Directory exists
            if not os.path.exists(f"{ROOT_DIR}/{SEARCH_TERM_DIR}"):
                # Create the directory
                os.makedirs(f"{ROOT_DIR}/{SEARCH_TERM_DIR}")
                print(f"Directory '{SEARCH_TERM_DIR}' created.")
            else:
                print(f"Directory '{SEARCH_TERM_DIR}' already exists.")

            os.chdir(f"{ROOT_DIR}/{SEARCH_TERM_DIR}")

        # The following two lines are debuging only
        # Print the current working directory to verify the change
    #     print("2 Current Working Directory:", os.getcwd())

        # pp(result)
        # pp(result.get('items', []))

        # Print the document number being processed
        print("URL counter to scrap data: ", counter + 1)

        # Extract Metadata Information
        title = result.get('title')
        snippet = result.get('snippet')
        link = result.get('link')

        # Parse the URL
        parsed_url = urlparse(link)

        # Construct the base URL
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"


        # Extract Company Name
        company_name = extract_company_name(base_url)

        #The following lines of code is used to extract complete website content into the respective company folder
    #     # Create the directory
    #     os.makedirs(company_name, exist_ok=True)
    #     os.chdir(company_name)

    #     # Print the current working directory to verify the change
    #     print("3 Current Working Directory:", os.getcwd())

        # Print extracted information
        print(f"Title: {title}\nSnippet: {snippet}\nCompany URL: {base_url}\nCompany Name: {company_name}\nOriginal URL: {link}")

        # Check if the text contains ".pdf"
        if ".pdf" in link:

            fetch_pdf_content(link)
            File_Type = 'PDF'
            File_Name = link
            Download_Status = "Success"

        else:

            print("The text does not contain '.pdf'. Therefore extracting data from URL")
            # Fetch and print the full content of the webpage
            response = fetch_url_content(link)
            File_Type = 'URL'

            if response:
                # print(f"Full Content:\n{response}\n")

                print("Can fetch full content.\n")
                with open(MY_SEARCH + '_' + str(counter) + '_' + company_name + '.txt', 'w', encoding='utf-8') as file:
                    file.write(response)
                    File_Name = MY_SEARCH + '_' + str(counter) + '_' + company_name + '.txt'
                    Download_Status = "Success"
                print(" ")

            else:
                File_Name = 'None'
                Download_Status = "Failed"

                print("--> Failed to fetch full content.\n")

        # Metadata_DF_Final = Metadata_DF_Final._append(Metadata_DF)
        # Metadata_DF_Final.loc[len(Metadata_DF_Final)] = Metadata_DF

        # Define a new row as a dictionary
        new_row = {'Search Term': MY_SEARCH, 'Title': title, 'Company URL': base_url, 'Company Name': company_name, 
                   'Search Date': Search_Date, 'File Type': File_Type, 'File Name': File_Name, 'Download Status': Download_Status}
        # Append the row
        Metadata_DF_Final.loc[len(Metadata_DF_Final)] = new_row

        counter+=1
    
    # Change directory to work directory
    os.chdir(wrk_dir)
    # Print the current working directory to verify the change
    print("--> Current Working Directory:", os.getcwd())

    return Metadata_DF_Final

