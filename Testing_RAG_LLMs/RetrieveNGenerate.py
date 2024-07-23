#!/usr/bin/env python
# coding: utf-8

# In[90]:


# pip install boto3 --force-reinstall --quiet


# In[92]:


# Import the boto3 library for interacting with AWS services
import boto3

# Import Config from botocore.client for configuring AWS client settings
from botocore.client import Config

# Import the pandas library for data manipulation and analysis
import pandas as pd

# Import the pprint module for pretty-printing data structures
import pprint

# Import the os module for interacting with the operating system
import os

# Importing the datetime class from the datetime module to handle date and time objects
from datetime import datetime


# In[93]:


boto3_session = boto3.session.Session()
region_name = boto3_session.region_name

print("session", boto3_session)
print("AWS Region Name:", region_name)

# Configure Bedroack runtime agent client
bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_agent_client = boto3.client("bedrock-agent-runtime", region_name=region_name, config=bedrock_config)


# In[119]:


def RetrieveAndGenerate(
    TMPRT,
    MX_TKN,
    TOP_K,
    input: str,
    kbId: str,
    region: str = "us-east-1",
    sessionId: str = None,
    mdl_id: str = "anthropic.claude-v2:1",
):
    
    """ The function provide response to a question based on the question, prompt, and other input parameters as follows:

        TMPRT,  # Temperature for the model generation
        MX_TKN,  # Maximum number of tokens to generate
        TOP_K,  # Number of top predictions to consider
        input: str,  # Question to process
        kbId: str,  # Knowledge base ID
        region: str = "us-east-1",  # AWS region, default is "us-east-1"
        sessionId: str = None,  # Session ID, default is None
        mdl_id: str = "anthropic.claude-v2:1",  # LLM Model ID, default is "anthropic.claude-v2:1"

    """

    model_arn = f"arn:aws:bedrock:{region}::foundation-model/{mdl_id}"

    if sessionId:
        return bedrock_agent_client.retrieve_and_generate(
            input={"text": input},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kbId,
                    "modelArn": model_arn,
                    "generationConfiguration": { 
                        "inferenceConfig": {
                            "textInferenceConfig": {
                            "temperature": TMPRT,  
                            "topP": 0.5,
                            "maxTokens": MX_TKN
                            }
                        },
                        "additionalModelRequestFields" : {
                            "top_k": TOP_K
                        },
                    },
                },
            },
            sessionId=sessionId,
        )

    else:
        return bedrock_agent_client.retrieve_and_generate(
            input={"text": input},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kbId,
                    "modelArn": model_arn,
                    "generationConfiguration": { 
                        "inferenceConfig": {
                            "textInferenceConfig": {
                            "temperature": TMPRT,  
                            "topP": 0.5,
                            "maxTokens": MX_TKN
                            }
                        },
                        "additionalModelRequestFields" : {
                            "top_k": TOP_K
                        },
                    },
                },
            },
        )




