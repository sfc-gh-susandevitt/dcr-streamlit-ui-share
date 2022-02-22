
import io
from pathlib import Path

import streamlit as st
import snowflake.connector
import plotly.figure_factory as ff
import numpy as np
import altair as alt
import time as time
import pandas as pd
import requests
import toml
from PIL import Image


# Page config
st.set_page_config(page_title="snowdcr",page_icon="❄️")

# Load Lib
def get_project_root() -> str:
    return str(Path(__file__).parent)
# st.write(get_project_root()) 

@st.cache(ttl=300)
def load_image(image_name: str) -> Image:
    return Image.open(Path(get_project_root()) / f"references/{image_name}")


# Sidebar
sideb = st.sidebar
sideb.image(load_image("DCR_MP_GBO.png"),use_column_width=True)

# Potential Login Process
# sideb.header ("Account Login")
# sideb.text_input('Snowflake Account', value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, placeholder=None)
# sideb.text_input('User Name', value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, placeholder=None)
# sideb.text_input('Password', value="", max_chars=None, key=None, type="password", help=None, autocomplete=None, on_change=None, placeholder=None)

# Consumer Database Prefix
sideb.header ("Consumer Database Connection")
prefix = sideb.text_input('Database Prefix', value="DEMO")
sideb.button("Submit", key='login', help=None, on_click=None, args=None, kwargs=None)

# Sidebar choose page 
sideb.header ("Configuration Navigation")
persona = sideb.selectbox("", ('Consumer Request','Consumer Admin','Provider Admin'))

def run_query(query):
   with conn.cursor() as cur:
      cur.execute(query)
      # Return a Pandas DataFrame containing all of the results.
      df = cur.fetch_pandas_all()
      return df

if persona == 'Consumer Request':
      sideb.write('You are viewing the Consumer Request page.')
      
      # Connect to Consumer Account
      def init_connection():
         return snowflake.connector.connect(**st.secrets["snowcat"])
      
      conn = init_connection()      
      # Consumer Request Page
      st.title("Consumer Request")
      df_privbudget=run_query("select epsilon_remaining from DCR_"+prefix+"_APP.CLEANROOM.PRIVACY_BUDGET;")
      privbudget = df_privbudget['EPSILON_REMAINING'].head(1).item()
      st.text("Current Privacy Budget: "+ str("{:.2f}".format(privbudget)))
      
      # Load Templates into frame
      df_template = run_query("select template_name from DCR_"+prefix+"_APP.CLEANROOM.TEMPLATES;")
      options_template = st.selectbox('Select your template', df_template)
      
      # Load Dimensions into frame
      # To Do: replace available values query with jinja template scope
      if options_template:
         df_dimensions = run_query("select concat($$'$$,table1.value,$$'$$) from (select template_name, case when template_name = 'campaign_conversion' then 'c.pets|c.zip|p.status|p.age_band|c_conv.product|p_exp.campaign|p_exp.device_type'else 'c.pets|c.zip|p.status|p.age_band'end as dimensions from DCR_"+prefix+"_APP.CLEANROOM.TEMPLATES),table(split_to_table(dimensions,'|')) as table1 where template_name = lower('"+options_template+"') order by value;")
         options_dimensions = st.multiselect('Select dimensions', df_dimensions)
         dimension_array = ",".join(options_dimensions)         

      # Where Clause 
      where = st.text_input('Use SQL to write an optional where clause. Use double quotes around whole statement and $$ around field values.',value='" c.pets <> $$DOG$$ "',help='Use double quotes around your entire statement and $$ as single quotes as shown in the example.')
      where_clause = str(where).replace('"','')
     
      # Epsilon Entry
      epsilon = st.slider('Select Epsilon value (i.e., 0.1)',0.0,privbudget,0.1, 0.1)
      st.write('Your new privacy budget will be '+str("{:.2f}".format(privbudget-epsilon)))
      submitquery = st.button("Submit", key='submitquery', help=None, on_click=None, args=None, kwargs=None)   
      
      # Submit Query 
      if submitquery==True:
         if len(dimension_array):                 
            st.success("Your request has been submitted.")         
            ts_value =  run_query("select current_timestamp() as ts;")
            ts = str(ts_value['TS'].head(1).item()).replace('"','')
            df_request = run_query("call dcr_"+prefix+"_app.cleanroom.request('"+options_template+"',object_construct('dimensions',array_construct("+dimension_array+"),'where_clause','"+where_clause+"' , 'epsilon','"+str(epsilon)+"')::varchar,NULL,'"+ts+"');")
            df_status = str(df_request['REQUEST'].head(1).item()).replace('"','')
            if df_status[4:10]=='Approv':
               requestidstart = df_status.find(',',1)
               requestidend = df_status.find(',',requestidstart+1)
               requestid = df_status[requestidstart+3:requestidend].lstrip()

               if 'multiparty' in options_template.lower():
                  df_request_2 = run_query("call dcr_"+prefix+"_app_two.cleanroom.request('"+options_template+"',object_construct('dimensions',array_construct("+dimension_array+"),'where_clause','"+where_clause+"' , 'epsilon','"+str(epsilon)+"')::varchar,'"+requestid+"','"+ts+"');")
                  #st.write(df_request_2)
             
               while True:
                  # find the new request_id and use that here
                  df_results = run_query("select request:PROPOSED_QUERY::varchar as querytext from dcr_"+prefix+"_app.cleanroom.provider_log where request_id = '"+requestid+"';")
                  checkstatus = df_results.empty                  
                  if checkstatus==True:
                     with st.spinner('Request approval in progress...'):
                        time.sleep(5)
                     continue
                  st.success('Your request has been approved and is being processed.')
                  results_query = df_results['QUERYTEXT'].head(1).item()
                  break                   

              #Error Handling
               try:
                    error_check = run_query(results_query)
               except ValueError:
                     st.error("Please check your where clause for allowed values and structure.")
                     st.stop()
                
               while True:
                  results = run_query(results_query)                   
                  checkresults = results.empty
                  if checkresults==True:
                     with st.spinner('Result processing in progress...'):
                        time.sleep(1)
                     continue                  
                  st.success('Your results are ready.')
                  st.write(results)
                  break
                  
            else:
                 st.write("An error has occured.  Here are some details: "+df_request)               
         else:
               st.write("Please choose at least one dimension for this template.")
            

      
if persona == 'Consumer Admin':
      sideb.write('You are viewing the Consumer Admin page.')
      
      # Consumer Request Page
      st.title("Consumer Admin")
      st.header("Under Construction")

if persona == 'Provider Admin':
      sideb.write('You are viewing the Provider Admin page.')
      
      # Consumer Request Page
      st.title("Provider Admin")
      st.header("Under Construction")

