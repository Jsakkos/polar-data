import streamlit as st
import pandas as pd
import numpy as np
import json
import pandas as pd
from pathlib import Path
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
from plotly_calplot import calplot
import plotly.express as px


from utils import (
    load_config,
    save_config,
    pretty_print_json,
    save_json_to_file,
    polar_datetime_to_python_datetime_str,
    xml_to_dict,
)
from accesslink import AccessLink
from datetime import datetime
from pathlib import Path
import os

CONFIG_FILENAME = "config.yml"
DATA_DIR = Path("./data")
class PolarData():
    """Example application for Polar Open AccessLink v3."""

    def __init__(self):
        self.config = load_config(CONFIG_FILENAME)

        if "access_token" not in self.config:
            print("Authorization is required. Run authorization.py first.")
            return

        self.accesslink = AccessLink(
            client_id=self.config["client_id"],
            client_secret=self.config["client_secret"],
        )

        self.running = True
        self.check_available_data()



    def get_user_information(self):
        user_info = self.accesslink.users.get_information(
            user_id=self.config["user_id"], access_token=self.config["access_token"]
        )
        pretty_print_json(user_info)
        USER_DIR = DATA_DIR / "user_data"
        if not USER_DIR.is_dir():
            os.mkdir(USER_DIR)
        save_json_to_file(
            user_info,
            USER_DIR / f'user_data_{datetime.today().strftime("%Y-%m-%d")}.json',
        )

    def check_available_data(self):
        available_data = self.accesslink.pull_notifications.list()

        if not available_data:
            print("No new data available.")
            return

        for item in available_data["available-user-data"]:
            if item["data-type"] == "EXERCISE":
                self.get_exercises()
            elif item["data-type"] == "ACTIVITY_SUMMARY":
                self.get_daily_activity()
            elif item["data-type"] == "PHYSICAL_INFORMATION":
                self.get_physical_info()

    def revoke_access_token(self):
        self.accesslink.users.delete(
            user_id=self.config["user_id"], access_token=self.config["access_token"]
        )

        del self.config["access_token"]
        del self.config["user_id"]
        save_config(self.config, CONFIG_FILENAME)

        print("Access token was successfully revoked.")


    def get_exercises(self):
        transaction = self.accesslink.training_data.create_transaction(
            user_id=self.config["user_id"], access_token=self.config["access_token"]
        )
        if not transaction:
            print("No new exercises available.")
            return

        resource_urls = transaction.list_exercises()["exercises"]
        EXERCISE_DIR = DATA_DIR / "exercise"
        if not EXERCISE_DIR.is_dir():
            os.mkdir(EXERCISE_DIR)
        for url in resource_urls:
            exercise_summary = transaction.get_exercise_summary(url)
            gpx_data = transaction.get_gpx(url)
            tcx_data = transaction.get_tcx(url)
            hr_data = transaction.get_heart_rate_zones(url)
            samples_data = transaction.get_available_samples(url)
            sample_data = transaction.get_samples(url)

            time = polar_datetime_to_python_datetime_str(
                str(exercise_summary["start-time"])
            )
            save_json_to_file(
                exercise_summary, EXERCISE_DIR / f"summary_data_{time}.json"
            )
            if (
                gpx_data
            ):  # not empty dict. If there is no data, this variable will have '{}' value
                save_json_to_file(
                    xml_to_dict(gpx_data), EXERCISE_DIR / f"gpx_data_{time}.json"
                )
            if tcx_data:
                save_json_to_file(
                    xml_to_dict(tcx_data), EXERCISE_DIR / f"tcx_data_{time}.json"
                )
            if hr_data:
                save_json_to_file(hr_data, EXERCISE_DIR / f"hr_data_{time}.json")
            if samples_data:
                save_json_to_file(
                    samples_data, EXERCISE_DIR / f"samples_data_{time}.json"
                )
            if sample_data:
                save_json_to_file(
                    sample_data, EXERCISE_DIR / f"sample_data_{time}.json"
                )

        transaction.commit()

    def get_daily_activity(self):
        transaction = self.accesslink.daily_activity.create_transaction(
            user_id=self.config["user_id"], access_token=self.config["access_token"]
        )
        if not transaction:
            print("No new daily activity available.")
            return

        resource_urls = transaction.list_activities()["activity-log"]
        ACTIVITY_DIR = DATA_DIR / "activity"
        if not ACTIVITY_DIR.is_dir():
            os.mkdir(ACTIVITY_DIR)
        for url in resource_urls:
            activity_summary = transaction.get_activity_summary(url)

            save_json_to_file(
                activity_summary,
                ACTIVITY_DIR
                / f'daily_activity_data_{str(activity_summary["date"])}.json',
            )
        transaction.commit()

    def get_physical_info(self):
        transaction = self.accesslink.physical_info.create_transaction(
            user_id=self.config["user_id"], access_token=self.config["access_token"]
        )
        if not transaction:
            print("No new physical information available.")
            return
        PHYSICAL_DIR = DATA_DIR / "physical"
        resource_urls = transaction.list_physical_infos()["physical-informations"]
        if not PHYSICAL_DIR.is_dir():
            os.mkdir(PHYSICAL_DIR)
        try:
            for url in resource_urls:
                physical_info = transaction.get_physical_info(url)

                time = polar_datetime_to_python_datetime_str(
                    str(physical_info["created"])
                )
                save_json_to_file(
                    physical_info, PHYSICAL_DIR / f"physical_data{time}.json"
                )
            transaction.commit()
        except FileNotFoundError:
            print("Missing directory")

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
col1, col2 = st.columns([4, 1])


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
    data['Week'] = data['Date'].dt.isocalendar().week
    week_data=data.loc[data.Date.dt.year == option].groupby(['Week']).sum().reset_index()
    total_daily_training=data.loc[data.Date.dt.year == option].groupby('Date').sum().reset_index()
    fig2=px.bar(week_data,x='Week',y='Duration')
    fig2.update_layout(height=250)
    st.plotly_chart(fig2,use_container_width=True)
    st.header('Total calories')
    fig3=px.bar(week_data,x='Week',y='Calories')
    fig3.update_layout(height=250)
    st.plotly_chart(fig3,use_container_width=True)
with col2:
    st.header('YTD Stats')

    #YTD Stats
    ytd_training_time = pd.to_timedelta(data.loc[data.Date.dt.year == option,'Duration'].sum(),unit='m')
    seconds = ytd_training_time.seconds
    hours = seconds//3600
    minutes = (seconds//60)%60
    delta_training_time = data.loc[data.Date.dt.year == option,'Duration'].iloc[-1]

    st.metric(label='Training time',value=f'{hours} hrs {minutes} mins',delta=f'{delta_training_time:.0f} mins')
    ytd_calories = data.loc[data.Date.dt.year == option,'Calories'].sum()
    delta_calories = int(data.loc[data.Date.dt.year == option,'Calories'].iloc[-1])
    st.metric(label="Calories burned", value=ytd_calories, delta=delta_calories)
    ytd_sessions = data.loc[data.Date.dt.year == option,'Duration'].count()
    st.metric(label="Sessions", value=ytd_sessions)
    st.subheader('Sports')
    ytd_by_sport = data.loc[data.Date.dt.year == option].groupby(['Sport']).sum().reset_index()
    fig4=px.pie(ytd_by_sport,values='Duration',names='Sport')
    fig4.update_layout(margin=dict(l=0, r=0, t=0, b=0),height=600)
    fig4.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=0.9,
    xanchor="right",
    x=1
))
    st.plotly_chart(fig4,use_container_width=True)