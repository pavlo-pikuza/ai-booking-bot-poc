document.addEventListener("DOMContentLoaded", function () {
    fetchClients();
    fetchServices();
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

function downloadFile(data, filename, type) {
    const blob = new Blob([data], { type: type });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

