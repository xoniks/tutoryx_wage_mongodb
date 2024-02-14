
from pymongo.mongo_client import MongoClient
from pymongo import DESCENDING
import toml
import streamlit as st
import datetime
import hashlib

secrets = toml.load('secrets.toml')

uri = secrets['mongodb']['uri']

# Create a new client and connect to the server
client = MongoClient(uri)

db = client['worker_database']
workers_coll = db['workers']
wages_coll = db['wages']
users_coll = db['users']

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username, password):
    user = users_coll.find_one({'username':username})
    if user and user['password']==hash_password(password):
        return True
    else:
        return False


def generate_worker_id():
    last_worker = workers_coll.find_one(sort=[('_id', DESCENDING)])
    if last_worker:
        return last_worker["_id"]+1
    else:
        return 1


st.title("Worker Management System")


username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button('Sign In'):
    if authenticate(username, password):
        st.sidebar.success("Signed in")



    option = st.sidebar.radio("Select an option",("Register Worker",
                                                "Calculate Wages",
                                                "Show all wages"))

    if option == 'Register Worker':
        st.subheader("Register Worker")
        name  = st.text_input("Name")
        surname = st.text_input("Surname")
        date_of_birth = st.date_input("Date of birth", min_value=datetime.date(1960, 1, 1))

        if st.button('Register'):
            worker_id = generate_worker_id()
            worker = {'_id':worker_id,
                    'name':name,
                    'surname':surname,
                    'date_of_birth':str(date_of_birth)}
            workers_coll.insert_one(worker)
            st.success(f'Worker {worker_id} registered successfully!')

    elif option=='Calculate Wages':
        st.subheader("Calculate Wages")
        worker_id = st.sidebar.number_input("Worker id",min_value=1,step=1) 
        hours_worked = st.number_input("Hours worked", min_value=0, step=1)
        rate = st.number_input("Hourly Rate", min_value=0)
        month_year = st.date_input("Select month")
        if st.button("Calculate"):
            worker = workers_coll.find_one({"_id":worker_id})
            if worker:
                wage = hours_worked * rate
                wage_entry = {
                    "worker_id":worker_id,
                    "hours_worked":hours_worked,
                    "rate":rate,
                    "wage":wage,
                    "month_year":str(month_year)
                }
                wages_coll.insert_one(wage_entry)
                st.success(f"Wage calculated for {worker['name']} with id {worker_id}: ${wage:.2f}")
            else:
                st.error("Worker not found, please check correct worker id!")

    elif option=='Show all wages':

        st.subheader("Display wages record")
        wages_data = [{"Worker id": wage['worker_id'],
                    "Date":wage['month_year'],
                    "Wage":wage['wage']} for wage in wages_coll.find()
                    ]
        if wages_data:
            st.table(wages_data)
        else:
            st.info('No wages records')


else:
    st.sidebar.error("Invalid username or password")
    st.stop()
