import pandas as pd
import numpy as np
import requests
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from fuzzywuzzy import fuzz
import fastapi
import uvicorn

df = pd.read_csv("Crop_recommendation.csv")
new_df = df[~df['label'].isin(['muskmelon', 'coffee', 'mothbeans', 'chickpea'])]
labels = new_df['label'].unique()
new_df['label1'] = new_df['label'].replace(labels, list(range(len(labels))))


X = new_df.drop(['label', 'label1'], axis=1)
y = new_df['label1']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)



rfc = RandomForestClassifier(n_estimators=200)
rfc.fit(X_train, y_train)


agri_dataset=pd.read_csv("crop_data.csv")
agri_dataset.drop(['variety', 'arrival_date',
       'min_price', 'max_price'],axis=1,inplace=True)


#changing names of commodities accroding to requirement by considering samll , capital letters and spaces
similarity_threshold = 73

for i in range(len(labels)):
    for j in range(len(agri_dataset)):
        ratio = fuzz.ratio(agri_dataset.at[j,'commodity'], labels[i])
        if ratio >= similarity_threshold:
            agri_dataset.at[j,'commodity']=labels[i]


for i in range(len(agri_dataset)):
    if(agri_dataset.at[i,'commodity']=='Green Gram Dal (Moong Dal)'):
        agri_dataset.at[i,'commodity']='mungbean'
    elif(agri_dataset.at[i,'commodity']=='Black Gram Dal (Urd Dal)'):
        agri_dataset.at[i,'commodity']='blackgram'
    elif(agri_dataset.at[i,'commodity']=='Cowpea (Lobia/Karamani)'):
        agri_dataset.at[i,'commodity']='kidneybeans'
    elif(agri_dataset.at[i,'commodity']=='Lentil (Masur)(Whole)'):
        agri_dataset.at[i,'commodity']='lentil'
    elif(agri_dataset.at[i,'commodity']=='Pegeon Pea (Arhar Fali)'):
        agri_dataset.at[i,'commodity']='pigeonpeas'


agri_dataset = agri_dataset[agri_dataset["commodity"].isin(labels)]
agri_dataset.reset_index(inplace=True,drop=True)

agri_dataset1 = agri_dataset.groupby(['commodity']).mean()

df_r = pd.read_csv("district wise rainfall normal.csv")

#create an fast api app
app = fastapi.FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to the Agri-App"}


@app.get("/predict")
def predict(district,season,n,p,k,ph):
    rainfall = df_r.loc[df_r['DISTRICT'] == district.upper()].iloc[0]
    if season == 'Kharif':
        rainfall = rainfall['JUN'] + rainfall['JUL'] + rainfall['AUG'] + rainfall['SEP']
        url = "http://api.weatherapi.com/v1/future.json?key=3a60e22cd27e491a8ee165801231102&q={}&dt={}".format(district, '2023-07-01')
        response = requests.get(url)
        data = response.json()

        temp = data['forecast']['forecastday'][0]['day']['avgtemp_c']
        humidity = data['forecast']['forecastday'][0]['day']['avghumidity']
        
    elif season == 'Rabi':
        rainfall = rainfall['OCT'] + rainfall['NOV'] + rainfall['DEC'] + rainfall['JAN'] + rainfall['FEB'] + rainfall['MAR']
        url = "http://api.weatherapi.com/v1/future.json?key=3a60e22cd27e491a8ee165801231102&q={}&dt={}".format(district, '2023-10-01')
        response = requests.get(url)
        data = response.json()

        temp = data['forecast']['forecastday'][0]['day']['avgtemp_c']
        humidity = data['forecast']['forecastday'][0]['day']['avghumidity']
    else:
        rainfall = rainfall['APR'] + rainfall['MAY']
        url = "http://api.weatherapi.com/v1/future.json?key=3a60e22cd27e491a8ee165801231102&q={}&dt={}".format(district, '2023-04-01')
        response = requests.get(url)
        data = response.json()

        temp = data['forecast']['forecastday'][0]['day']['avgtemp_c']
        humidity = data['forecast']['forecastday'][0]['day']['avghumidity']


    single_data = np.array([n, p, k, temp,humidity, ph, rainfall])
    single_data = single_data.reshape(1,-1)

    top_5 = rfc.predict_proba(single_data).argsort()[0][-5:][::-1]

    top_5_labels = [labels[i] for i in top_5]

    diff = top_5[0] - top_5[1]
    if diff > 0.2:
        return {"Recommended crop is: ": top_5_labels[0]}
    else:
        #compare modal price of top 3 crops
        price1 = agri_dataset1['modal_price'][top_5_labels[0]]
        price2 = agri_dataset1['modal_price'][top_5_labels[1]]
        price3 = agri_dataset1['modal_price'][top_5_labels[2]]
        if price1 < price2 and price1 < price3:
            return {"Recommended crop is: ": top_5_labels[0]}

        elif price2 < price1 and price2 < price3:
            return {"Recommended crop is: ": top_5_labels[1]}

        else:
            return {"Recommended crop is: ": top_5_labels[2]}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
