from datetime import datetime, timedelta, time
import pandas as pd
import random
import bisect
import plotly.express as px
from plotly import graph_objects as go 

def time_add(time_obj: time, minutes: int):
    delta = timedelta(minutes=minutes)
    new_time = (datetime.combine(datetime.today().date(), time_obj) + delta).time()
    return new_time

def appoinments_gen(count, clients, services, work_days, work_hour_start, work_hour_end, break_time):

    appointments = []
    res = []

    print("📌 Generating non-overlapping appointments...")

    while len(appointments) < count:
        client = random.choice(clients)
        service = random.choice(list(services.keys()))
        duration = services[service]
        day = random.choice(work_days)
        hour = random.randint(work_hour_start, work_hour_end - 1)
        minute = random.choice([0, 0, 0, 10, 20, 30, 30, 40, 50])

        start_time = datetime.strptime(f'{hour}:{minute}', "%H:%M").time()
        end_time = time_add(start_time,  duration)

        overlap = any(
            (appo['day'] == day) and (
                (start_time >= appo['start_time'] and start_time < time_add(appo['end_time'], break_time)) or
                (time_add(end_time, break_time) > appo['start_time'] and end_time <= appo['end_time'])
            )
            for appo in appointments
        )

        is_late = True if end_time > datetime.strptime(work_hour_end, "%H:%M").time() else False

        duplicate = any(
            (appo['day'] == day and appo['client_id'] == client and appo['service_id'] == service)
            for appo in appointments
        )

        todays_appos = sorted(
            [appo for appo in appointments if appo["day"] == day],
            key=lambda x: x["start_time"]
        )

        prev_appo = None
        next_appo = None
        if todays_appos:
            start_times = [appo["start_time"].isoformat() for appo in todays_appos]

            idx = bisect.bisect_right(start_times, start_time.strftime("%H:%M"))

            if idx > 0:
                prev_appo = todays_appos[idx - 1]

            if idx < len(todays_appos):
                next_appo = todays_appos[idx]
        
        long_waiting = False
        if prev_appo is not None:
            if prev_appo['client_id'] == client and time_add(prev_appo['end_time'], break_time) > start_time:
                long_waiting = True

        if next_appo is not None:
            if next_appo['client_id'] == client and time_add(end_time, break_time) > next_appo['start_time']:
                long_waiting = True 

        if not overlap and not duplicate and not is_late and not long_waiting:
            appointments.append({
                'day': day,
                'start_time': start_time,
                'end_time': end_time,
                'service_id': service,
                'duration': duration,
                'client_id': client
            })

            res.append({
                'client_id': client,
                'service_id': service,
                'start_time': start_time,
                'day': day
            })

    for app in appointments:
        app['start_time'] = app['start_time'].strftime("%H:%M")
        app['end_time'] = app['end_time'].strftime("%H:%M")

    for r in res:
        r['start_time'] = r['start_time'].strftime("%H:%M")

    return res, appointments



def shedule_plot(df, current_day:str, current_time:time, output_file="static/schedule_plot.html"):
    day_map = {
        "Monday":5,
        "Tuesday":4,
        "Wednesday":3,
        "Thursday":2,
        "Friday":1
    }

    current_time_dt = pd.to_datetime(current_time.strftime("%H:%M"), format="%H:%M")

    df["start_time_dt"] = pd.to_datetime(df["start_time"], format="%H:%M")
    df["end_time_dt"] = pd.to_datetime(df["end_time"], format="%H:%M")
    df["day_start"] = df["day"].apply(lambda x: day_map.get(x) - 0.46)
    df["day_end"] = df["day"].apply(lambda x: day_map.get(x) + 0.46)
    
    unique_services = df["service"].unique()
    unique_clients = df["client"].unique()

    available_colors = ["blue", "orange", "green", "red", "pink", "cyan"]
    available_patterns = ["", "/", "\\", "-", "|", "+"]

    pattern_styles = {service: available_patterns[i % len(available_patterns)] for i, service in enumerate(unique_services)}
    color_styles = {client: available_colors[i % len(available_colors)] for i, client in enumerate(unique_clients)}

    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["start_time_dt"], row["end_time_dt"], row["end_time_dt"], row["start_time_dt"], row["start_time_dt"]],
            y=[row["day_start"], row["day_start"], row["day_end"], row["day_end"], row["day_start"]],
            mode="lines",
            fill="toself",
            fillpattern=dict(shape=pattern_styles.get(row["service"]), size=5),
            line=dict(color=color_styles.get(row['client']), width=2),
            hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter(
            x=[row["start_time_dt"], row["end_time_dt"]],
            y=[(row["day_start"] + row["day_end"]) / 2] * 2,
            mode="text",
            text=[f"<b>  {row['client']}<br>  {row['service']}<br>  ({row['start_time']}-<br>  -{row['end_time']})</b>"],
            textposition="middle right",
            showlegend=False,
            hoverinfo="skip"
        ))

    fig.update_layout(
        title="Weekly Shedule",
        margin=dict(l=20, r=30, t=50, b=30),
        xaxis=dict(
            tickformat="%H:%M",
            title="",
            range=[pd.to_datetime("08:55", format="%H:%M"), pd.to_datetime("16:05", format="%H:%M")],
        ),
        yaxis=dict(
            range=[0.4, 5.6], 
            title="",
            tickvals=list(day_map.values()),
            ticktext=list(day_map.keys()),
            ),
        showlegend=False,
    )

    fig.add_trace(go.Scatter(
        x=[current_time_dt, current_time_dt],
        y=[day_map.get(current_day) - 0.48, day_map.get(current_day) + 0.48],
        mode="lines+markers",
        marker=dict(size=10, color="red", symbol="circle"),
        name="Current Time",
        hovertemplate="<b>Current Time<br>%{x|%H:%M}",
        hovertext="None"
    ))

    #fig.show()
    fig.write_html(output_file)
