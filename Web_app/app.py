# import libraries
import streamlit as st
import pandas as pd
import boto3
import pymysql
import json

st.set_page_config(page_title="Amazon Sales Dashboard", layout="wide")

def set_fun_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Fredoka', sans-serif;
            color: #2e2e2e;
        }

        .stApp {
            background: linear-gradient(to bottom right, #f6d365, #fda085);
            background-attachment: fixed;
        }

        /* Button styling */
        .stButton > button {
            background-color: #ff69b4;
            color: white;
            border: none;
            border-radius: 30px;
            padding: 0.6em 1.2em;
            font-weight: bold;
            transition: 0.3s ease-in-out;
        }

        .stButton > button:hover {
            background-color: #ff1493;
            transform: scale(1.05);
        }

        /* Section headers */
        h1, h2, h3 {
            color: #ff4b5c;
        }

        /* Wider layout for comfort */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Call the theme function right after page config
set_fun_theme()


# connect to rawdata s3 bucket
BUCKET_NAME = 'ds4300rawdata'

# create s3 client to connect to aws s3 and allow for upload 
s3_client = boto3.client('s3')

# set the page title
st.title("Amazon Sales Transaction Dashboard YO")

# section 1: upload json file to s3
st.header("Step 1: Upload your sales data (JSON format)")

# upload file through the streamlit ui
uploaded_file = st.file_uploader("Choose a JSON file", type="json")

# if a file is uploaded, show a preview and upload button
if uploaded_file is not None:
    try:
        json_data = json.load(uploaded_file)
        df = pd.DataFrame(json_data)
        st.write("Preview of uploaded file:")
        st.dataframe(df)

        if st.button("Upload to S3"):
            uploaded_file.seek(0)
            
            s3_key = f"uploads/{uploaded_file.name}"
            s3_client.upload_fileobj(uploaded_file, BUCKET_NAME, s3_key)
            st.success(f"Uploaded {uploaded_file.name} to S3 bucket '{BUCKET_NAME}' under 'uploads/'")
           


            
    except Exception as e:
        st.error(f"Could not read JSON file: {e}")

# section 2: load sales data from rds and display dashboard
st.header("Step 2: Load sales dashboard (from RDS)")

# use session_state to persist loaded data
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# function to connect to rds and load sales data from database
def load_data_from_rds():
    try:
        conn = pymysql.connect(
            host='sales-cleaned-db.cjywqmyqm23a.us-east-2.rds.amazonaws.com',
            user='admin',
            password='ds4300finalproject',
            database='salesdb'
        )
        df = pd.read_sql("SELECT * FROM products_cleaned", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Failed to connect to RDS: {e}")
        return pd.DataFrame()

# Load dashboard button
if st.button("Load Dashboard"):
    st.session_state.data = load_data_from_rds()
    st.session_state.data_loaded = True

# Display charts only if data is available
if st.session_state.data_loaded:
    data = st.session_state.data

    st.subheader("Total Number of Products by Category")
    category_counts = data['category'].value_counts()
    st.bar_chart(category_counts)

    st.subheader("Average Discount Percentage by Category")
    avg_discount = data.groupby('category')['discount_percentage'].mean().sort_values(ascending=False)
    st.bar_chart(avg_discount)

    st.subheader("Average Rating by Category")
    avg_rating = data.groupby('category')['rating'].mean().sort_values(ascending=False)
    st.line_chart(avg_rating)

    # Drilldown per category
    st.subheader("Explore Individual Category")
    unique_categories = sorted(data['category'].dropna().unique())
    selected_category = st.selectbox("Select a category to explore:", unique_categories)

    if selected_category:
        filtered = data[data['category'] == selected_category]
        st.write(f"Total products in '{selected_category}': {len(filtered)}")

        # Summary metrics
        avg_discount = filtered['discount_percentage'].mean()
        st.metric(label="Average Discount %", value=f"{avg_discount:.2%}" if pd.notna(avg_discount) else "N/A")

        avg_rating = filtered['rating'].mean()
        st.metric(label="Average Rating", value=f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A")

        # Top 5 rated products
        st.subheader("Top 5 Rated Products")
        top_rated = filtered.sort_values(by='rating', ascending=False).head(5)[['product_name', 'rating']]
        st.dataframe(top_rated)
