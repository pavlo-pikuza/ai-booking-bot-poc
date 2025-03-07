from datetime import datetime, timedelta
import random
import bisect
import plotly.express as px

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
        minute = random.choice([0,0,0, 10, 20, 30, 30, 40, 50])

        start_time = datetime.strptime(day, "%A").replace(hour=hour, minute=minute, second=0)
        end_time = start_time + timedelta(minutes=duration)

        overlap = any(
            (appo['day'] == day) and (
                (start_time >= appo['start_time'] and start_time < appo['end_time'] + timedelta(minutes = break_time)) or
                (end_time > appo['start_time'] - timedelta(minutes = break_time) and end_time <= appo['end_time'])
            )
            for appo in appointments
        )

        is_late = True if end_time > datetime.strptime(day, "%A").replace(hour=16, minute=0, second=0) else False

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


def shedule_plot(df,  output_file="static/schedule_plot.html"):
    week_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    fig = px.timeline(
        df,
        x_start="start_time",
        x_end="end_time",
        y="day",
        color="client",
        pattern_shape="service",
        title="Client Appointments Schedule",
        labels={"day": ""},
        text = "client",
        category_orders={"day": week_order} 
    )
    fig.update_traces(
        textposition='inside',
        marker=dict(line=dict(color='black', width=1))
    )
    fig.update_coloraxes(showscale=False)

    fig.update_xaxes(
        tickformat="%H:%M",
        tickformatstops=[
            dict(dtickrange=[0, 30 * 60 * 1000], value="%H:%M"),
            dict(dtickrange=[30 * 60 * 1000, 60 * 60 * 1000], value="%H:%M"),
            dict(dtickrange=[60 * 60 * 1000, 24 * 60 * 60 * 1000], value="%H:%M"),
        ],
        dtick=60 * 60 * 1000,
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.3)",
        gridwidth=1
    )

    fig.add_shape(
        dict(
            type="line",
            x0="09:00",
            x1="09:00",
            y0=-0.5,
            y1=4.5,
            line=dict(color="red", width=2, dash="dot"),
        )
    )

    fig.write_html(output_file)