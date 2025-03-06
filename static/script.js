document.addEventListener("DOMContentLoaded", function () {
    fetchClients();
    fetchServices();
    fetchAppointments();
});

function fetchClients() {
    fetch('/clients')
        .then(response => response.json())
        .then(data => {
            const clientSelector = document.querySelector('.client-selector');
            clientSelector.innerHTML = '';
            data.forEach(client => {
                const option = document.createElement('option');
                option.value = client.id;
                option.textContent = client.name;
                clientSelector.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading clients:', error));
}

function fetchServices() {
    fetch('/services')
        .then(response => response.json())
        .then(data => {
            const scheduleTitle = document.querySelector('.schedule h2');
            const servicesList = document.createElement('ul');
            data.forEach(service => {
                const li = document.createElement('li');
                li.textContent = `${service.name} (${service.duration} min)`;
                servicesList.appendChild(li);
            });
            scheduleTitle.appendChild(servicesList);
        })
        .catch(error => console.error('Error loading services:', error));
}

function fetchAppointments() {
    fetch('/appointments')
        .then(response => response.json())
        .then(data => {
            drawSchedule(data);
        })
        .catch(error => console.error('Error loading appointments:', error));
}

function drawSchedule(appointments) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    let traces = {};

    appointments.forEach(appointment => {
        const dayIndex = new Date(appointment.start_time).getDay() - 1;
        if (dayIndex < 0 || dayIndex > 4) return;

        const hour = new Date(appointment.start_time).getHours();
        const clientName = appointment.client_name;

        if (!traces[clientName]) {
            traces[clientName] = {
                x: [],
                y: [],
                mode: 'markers',
                marker: { size: 12 },
                name: clientName
            };
        }
        
        traces[clientName].x.push(days[dayIndex]);
        traces[clientName].y.push(hour);
    });

    Plotly.newPlot('schedule-plot', Object.values(traces), {
        title: 'Appointments Schedule',
        xaxis: { title: 'Days' },
        yaxis: { title: 'Hours', tickvals: [9, 10, 11, 12, 13, 14, 15, 16] }
    });
}