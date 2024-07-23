#!/usr/bin/env python
# coding: utf-8

# In[5]:


# Importing the time module to handle time-related functions
import time

# Importing the datetime class from the datetime module to handle date and time objects
from datetime import datetime


# In[14]:


def get_DateTime():
    # Get the current date and time
    current_datetime = datetime.now()

    # Format the date and time
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    return formatted_datetime


# In[15]:


def get_Date():
    # Get the current date and time
    current_datetime = datetime.now()

    # Format the date and time
    formatted_date = current_datetime.strftime("%Y-%m-%d")
    
    return formatted_date


# In[12]:


def Time():
    return (time.time())

