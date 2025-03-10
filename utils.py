from datetime import datetime, timedelta
import pandas as pd
import random
import bisect
import plotly.express as px
from plotly import graph_objects as go 

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

        start_time = datetime.strptime('1970-01-05', "%Y-%m-%d").replace(hour=hour, minute=minute, second=0)
        end_time = start_time + timedelta(minutes=duration)

        overlap = any(
            (appo['day'] == day) and (
                (start_time >= appo['start_time'] and start_time < appo['end_time'] + timedelta(minutes = break_time)) or
                (end_time > appo['start_time'] - timedelta(minutes = break_time) and end_time <= appo['end_time'])
            )
            for appo in appointments
        )

        is_late = True if end_time > datetime.strptime('1970-01-05', "%Y-%m-%d").replace(hour=16, minute=0, second=0) else False

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
            start_times = [appo["start_time"] for appo in todays_appos]

            idx = bisect.bisect_right(start_times, start_time)

            if idx > 0:
                prev_appo = todays_appos[idx - 1]

            if idx < len(todays_appos):
                next_appo = todays_appos[idx]
        
        long_waiting = False
        if prev_appo is not None:
            if prev_appo['client_id'] == client and (start_time - prev_appo['end_time']).total_seconds() > break_time * 60:
                long_waiting = True

        if next_appo is not None:
            if next_appo['client_id'] == client and (next_appo['start_time'] - end_time).total_seconds() > break_time * 60:
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

    return res, appointments



def shedule_plot(df, current_time, output_file="static/schedule_plot.html"):
    day_map = {
        "Monday":5,
        "Tuesday":4,
        "Wednesday":3,
        "Thursday":2,
        "Friday":1
    }

    df["start_time_dt"] = pd.to_datetime(df["start_time"], format="%H:%M")
    df["end_time_dt"] = pd.to_datetime(df["end_time"], format="%H:%M")
    df["day_start"] = df["day"].apply(lambda x: day_map.get(x) - 0.46)
    df["day_end"] = df["day"].apply(lambda x: day_map.get(x) + 0.46)

    current_day = current_time.strftime("%A")
    current_time = datetime.strptime(current_time.strftime("%H:%M"), "%H:%M")
    
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
            text=[f"<b>  {row['client']}<br>  {row['service']}<br>  ({row['start_time']}-<br>  -{row['end_time']})</b>"],  # Сам текст
            textposition="middle right",
            showlegend=False,
            hoverinfo="skip"
        ))

    fig.update_layout(
        title="Weekly Shedule",
        xaxis=dict(
            tickformat="%H:%M",
            title="Time",
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
        x=[current_time, current_time],
        y=[day_map.get(current_day) - 0.48, day_map.get(current_day) + 0.48],
        mode="lines+markers",
        marker=dict(size=10, color="red", symbol="circle"),
        name="Current Time",
        hovertemplate="<b>Current Time<br>%{x|%H:%M}",
        hovertext="None"
    ))

    #fig.show()
    fig.write_html(output_file)
