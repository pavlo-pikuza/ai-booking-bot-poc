function drawSchedule() {
    let trace1 = {
        x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        y: [9, 10, 11, 12, 13, 14, 15, 16],
        mode: 'markers',
        marker: { size: 12 }
    };
    let layout = {
        title: 'Appointments Schedule',
        xaxis: { title: 'Days' },
        yaxis: { title: 'Hours', tickvals: [9, 10, 11, 12, 13, 14, 15, 16] }
    };
    Plotly.newPlot('schedule-plot', [trace1], layout);
}

document.addEventListener("DOMContentLoaded", function () {
    drawSchedule();
});
