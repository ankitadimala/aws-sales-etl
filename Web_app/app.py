# import libraries
import streamlit as st
import pandas as pd
import boto3
import pymysql
import json

# connect to rawdata s3 bucket
BUCKET_NAME = 'ds4300rawdata'

# create s3 client to connect to aws s3 and allow for upload 
s3_client = boto3.client('s3')

# set the page title
st.title("Amazon Sales Transaction Dashboard YO")

# section 1: upload json file to s3
st.header("step 1: upload your sales data (json format)")

# upload file through the streamlit ui
uploaded_file = st.file_uploader("choose a json file", type="json")

# if a file is uploaded, show a preview and upload button
if uploaded_file is not None:
    # read the json file into a pandas dataframe
    try:
        json_data = json.load(uploaded_file)
        df = pd.DataFrame(json_data)
        st.write("preview of uploaded file:")
        st.dataframe(df)

        # upload to s3 when user clicks the button
        if st.button("upload to s3"):
            uploaded_file.seek(0)  # reset file pointer before uploading
            s3_client.upload_fileobj(uploaded_file, BUCKET_NAME, uploaded_file.name)
            st.success(f"uploaded {uploaded_file.name} to s3 bucket '{BUCKET_NAME}'")
    except Exception as e:
        st.error(f"could not read json file: {e}")

# section 2: load sales data from rds and display dashboard
st.header("step 2: load sales dashboard (from rds)")

# function to connect to rds and load sales data from database
def load_data_from_rds():
    try:
        # connect to mysql rds instance
        conn = pymysql.connect(
            host='sales-cleaned-db.cjywqmyqm23a.us-east-2.rds.amazonaws.com',       # replace with your actual rds endpoint
            user='admin',
            password='ds4300finalproject',
            database='salesdb'
        )
        # read data from table into pandas dataframe
        df = pd.read_sql("SELECT * FROM products_cleaned", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"failed to connect to rds: {e}")
        return pd.DataFrame()


# if user clicks the load dashboard button, show charts
if st.button("load dashboard"):
    data = load_data_from_rds()
    if not data.empty:
        st.subheader("📦 Total Number of Products by Category")
        category_counts = data['category'].value_counts()
        st.bar_chart(category_counts)

        st.subheader("💸 Average Discount Percentage by Category")
        avg_discount = data.groupby('category')['discount_percentage'].mean().sort_values(ascending=False)
        st.bar_chart(avg_discount)

        st.subheader("⭐ Average Rating by Category")
        avg_rating = data.groupby('category')['rating'].mean().sort_values(ascending=False)
        st.line_chart(avg_rating)
    else:
        st.warning("no data available.")
