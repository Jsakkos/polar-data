import streamlit as st
import pandas as pd
import numpy as np
import json
import pandas as pd
from pathlib import Path
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from plotly_calplot import calplot
import plotly.express as px

def polar_datetime_to_python_datetime_str(polar_dt):
    new_dt = polar_dt.replace("T", " ")
    date_time_obj = datetime.strptime(new_dt, "%Y-%m-%d %H:%M:%S.%f")

    return date_time_obj.strftime("%Y-%m-%d+%H_%M_%S_%f")
def polar_time_conversion(polar_t):
    return timedelta(seconds=int(float(polar_t.replace("PT", "").replace("S", "")))) /timedelta(minutes=1)

def load_data():
    DIR = Path(r"data/user_data")
    files = sorted(DIR.glob("training-session*.json"))
    dfs = list()
    for file in files:
        with open(file, "r") as f:
            data = json.load(f)
            if "kiloCalories" in data.keys():
                dfs.append(
                    pd.DataFrame(
                        [
                            [
                                data["kiloCalories"],
                                polar_datetime_to_python_datetime_str(
                                    data["exercises"][0]["startTime"]
                                ).split("+")[0],
                                data["exercises"][0]["sport"],
                                polar_time_conversion(data["exercises"][0]["duration"]),
                            ]
                        ],
                        columns=["Calories", "Date", "Sport", "Duration"],
                    )
                )

    df = pd.concat(dfs)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


st.set_page_config(layout="wide")
col1, col2 = st.columns([3, 1])


data = load_data()
option =st.sidebar.selectbox('Year',data.Date.dt.year.unique(),index=len(data.Date.dt.year.unique())-1)
total_daily_calories = (
    data.loc[data.Date.dt.year == option].groupby("Date").sum().reset_index()
)
fig = calplot(
    total_daily_calories,
    x="Date",
    y="Calories",
    name="Calories",
    colorscale="purples",
    month_lines_width=2,
    month_lines_color="#d9d9d9",
)
fig.update_layout(height=250)
with col1:
    st.title("Calories burned per day")
    st.plotly_chart(fig,use_container_width=True)
    st.title("Weekly summaries")
    st.header('Training time')
    total_daily_training=data.loc[data.Date.dt.year == option].groupby('Date').sum().reset_index()
    fig2=px.line(total_daily_training,x='Date',y='Duration')
    fig2.update_layout(height=250)
    st.plotly_chart(fig2,use_container_width=True)
    st.header('Total calories')
    fig3=px.line(total_daily_training,x='Date',y='Calories')
    fig3.update_layout(height=250)
    st.plotly_chart(fig3,use_container_width=True)
with col2:
    st.header('YTD Stats')

    #YTD Stats
    st.subheader('Training time'), st.text(pd.to_timedelta(data.loc[data.Date.dt.year == option,'Duration'].sum(),unit='m'))
    'Calories burned', data.loc[data.Date.dt.year == option,'Calories'].sum()