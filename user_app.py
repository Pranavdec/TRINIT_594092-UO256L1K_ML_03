import streamlit as st
import requests

#dont display error messages
st.set_option('deprecation.showfileUploaderEncoding', False)



st.title('Crop Recommendation System')

st.write('''
## About
This is a crop recommendation system based on the rainfall and temperature of the district.
''')

# take input from the user
def user_input_features():
   #show a input box for the user to enter the district name
    district = st.sidebar.text_input("Enter the district name")
    district = district.upper()
    #show a dropdown for the user to select the season
    season = st.sidebar.selectbox('Select the season',('Kharif','Rabi','Summer'))
    #show a input box for the user to enter the Nitrogen value
    n = st.sidebar.text_input("Enter the Nitrogen value")
    if n!='':
        n = float(n)
    #show a input box for the user to enter the Phosphorous value
    p = st.sidebar.text_input("Enter the Phosphorous value")
    if p!='':
        p = float(p)
    #show a input box for the user to enter the Potassium value
    k = st.sidebar.text_input("Enter the Potassium value")
    if k!='':
        k = float(k)
    #show a input box for the user to enter the pH value
    ph = st.sidebar.text_input("Enter the pH value")
    if ph!='':
        ph = float(ph)
    
    #call the api to get output
    url = "http://127.0.0.1:8000/predict?district={}&season={}f&n={}&p={}&k={}&ph={}".format(district,season,n,p,k,ph)

    #click on the button to get the output , place the button below the input fields
    if st.sidebar.button("Predict"):
        #check if all the input fields are filled
        if district == '' or season == '' or n == '' or p == '' or k == '' or ph == '':
            st.write('Please fill all the input fields')
        else:
            response = requests.get(url)
            data = response.json()
            return data



df = user_input_features()
#display the output
st.subheader('Recommended crop is:')
if df is not None:
    st.write(df['Recommended crop is: '])

