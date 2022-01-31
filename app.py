import streamlit as st
import pandas as pd
import numpy as np
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import calplot

def polar_datetime_to_python_datetime_str(polar_dt):
    new_dt = polar_dt.replace('T', ' ')
    date_time_obj = datetime.strptime(new_dt, '%Y-%m-%d %H:%M:%S.%f')

    return date_time_obj.strftime('%Y-%m-%d+%H_%M_%S_%f')
@st.cache
def load_data():
    DIR = Path(r'data/user_data')
    files=sorted(DIR.glob('training-session*.json'))
    dfs = list()
    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)
            if 'kiloCalories' in data.keys():
                dfs.append(pd.DataFrame([[data['kiloCalories'],polar_datetime_to_python_datetime_str(data['exercises'][0]['startTime']).split('+')[0]]],columns=['Calories','Date']))

    df = pd.concat(dfs)
    df['Date']=pd.to_datetime(df['Date'])
    return df

st.title('Calories burned per day')
data=load_data()
data.set_index('Date',inplace=True)
st.subheader('Raw data')
st.write(data)
st.pyplot(calplot.calplot(data['Calories']))