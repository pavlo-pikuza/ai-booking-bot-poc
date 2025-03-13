document.addEventListener("DOMContentLoaded", function () {
    fetchServices();
    fetchClientList();
    fetchClients();

    const clock = document.getElementById("clock");

    let isRunning = true;
    let timeUpdater = null;


    fetch("/time")
        .then(response => response.json())
        .then(data => {
            updateClockAppearance(data.status);
            handleTimeUpdates(isRunning);
        });

    clock.addEventListener("click", toggleClock);

    function updateTimeAndPlot() {
        fetch("/time")
            .then(response => response.json())
            .then(data => {
                if (!data.time) return;

                const time = data.time;
                const day = data.day;
                const [hours, minutes] = time.split(":");
                updatePlot()
                clock.innerHTML = `<div class="clock-time">${hours}<span id="colon">:</span>${minutes}</div><div class="clock-day">${day}</div>`;
                updateClockAppearance(data.status);
            })
            .catch(error => console.error("Error fetching time:", error));
    }

    function toggleClock() {
        fetch("/time", { 
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ action: "toggle" })
        })
            .then(response => response.json())
            .then(data => {
                isRunning = data.status === "running";
                updateClockAppearance(isRunning);
                handleTimeUpdates(isRunning);
            })
            .catch(error => console.error("Error toggling clock:", error));
    }

    function updateClockAppearance(isRunning) {
        const colon = document.getElementById("colon");
        if (isRunning) {
            clock.classList.remove("clock-stopped");
            clock.setAttribute("title", "Stop");
            if (colon) colon.classList.add("blink");
        } else {
            clock.classList.add("clock-stopped");
            clock.setAttribute("title", "Start");
            if (colon) colon.classList.remove("blink");
        }
    }

    function updatePlot() {
        const oldFrame = document.getElementById("plot-frame");
    
        if (!oldFrame) return;
    
        const newFrame = document.createElement("iframe");
        newFrame.id = "plot-frame";
        newFrame.style.position = "absolute";
        newFrame.style.top = oldFrame.offsetTop + "px";
        newFrame.style.left = "0";
        newFrame.style.width = oldFrame.clientWidth + "px";
        newFrame.style.height = oldFrame.clientHeight + "px";
        newFrame.style.opacity = "0";
        newFrame.src = `/static/schedule_plot.html?t=${new Date().getTime()}`;
    
        oldFrame.parentNode.appendChild(newFrame);
    
        newFrame.onload = function () {
            newFrame.style.transition = "opacity 0.5s";
            newFrame.style.opacity = "1";

            setTimeout(() => {
                oldFrame.remove();
            }, 500);
        };
    }


    function handleTimeUpdates(isRunning) {
        if (isRunning) {
            if (!timeUpdater) {
                updateTimeAndPlot();
                timeUpdater = setInterval(updateTimeAndPlot, 5000);
            }
        } else {
            clearInterval(timeUpdater);
            timeUpdater = null;
        }
    }


    // manual time change
    const timeModal = document.getElementById("time-modal");
    const openTimeModal = document.getElementById("open-time-modal");
    const closeTimeModal = document.getElementById("close-time-modal");
    const setTimeBtn = document.getElementById("set-time-btn");

    setTimeBtn.addEventListener("click", function () {
        const selectedDay = document.getElementById("day-select").value;
        const selectedHour = document.getElementById("hour-input").value;
        const selectedMinute = document.getElementById("minute-input").value;

        fetch("/time", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                action: "set",
                time: `${selectedDay} ${selectedHour}:${selectedMinute}`
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Time updated successfully!");
                timeModal.style.display = "none";
                updateTimeAndPlot();
            } else {
                alert("Error updating time.");
            }
        })
        .catch(error => console.error("Error setting time:", error));
    });

    document.getElementById("chat-send").addEventListener("click", function () {
        sendMessage();
    });

    function sendMessage() {
        const messageInput = document.querySelector(".chat-input input");
        const message = messageInput.value.trim();
        const clientId = document.querySelector(".client-selector").value;
    
        if (!message || !clientId) {
            alert("Please select a client and type a message.");
            return;
        }
    
        fetch("/send_message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ client_id: clientId, message: message, is_client_sender: true })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error:", data.error);
                return;
            }
    
            // 1️⃣ Добавляем сообщение в историю чата
            addMessageToChat(clientId, data.message, data.timestamp);
    
            // 2️⃣ Очищаем поле ввода
            messageInput.value = "";
    
            // 3️⃣ Запускаем обработку чата (если нужно)
            processChat();
        })
        .catch(error => console.error("Error sending message:", error));
    }
    
    function loadChatHistory(clientId) {
        fetch(`/chat_history/${clientId}`)
        .then(response => response.json())
        .then(messages => {
            const chatHistory = document.querySelector(".chat-history");
            chatHistory.innerHTML = ""; // Очищаем историю перед загрузкой
    
            messages.forEach(msg => {
                addMessageToChat(clientId, msg.message, msg.timestamp);
            });
        })
        .catch(error => console.error("Error loading chat history:", error));
    }
    
    function addMessageToChat(clientId, message, timestamp) {
        const chatHistory = document.querySelector(".chat-history");
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message");
        messageDiv.innerHTML = `<b>Client ${clientId}:</b> ${message} <span class="timestamp">(${timestamp})</span>`;
        chatHistory.appendChild(messageDiv);
    }
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

function fetchClients() {
    fetch("/clients")
        .then(response => response.json())
        .then(data => {
            const select = document.querySelector(".client-selector");
            select.innerHTML = "";

            data.forEach(client => {
                let option = document.createElement("option");
                option.value = client.id;
                option.textContent = client.name;
                select.appendChild(option);
            });
        })
        .catch(error => console.error("Error loading clients:", error));
}


function fetchClientList() {
    fetch('/clients')
        .then(response => response.json())
        .then(clients => {
            const clientList = document.getElementById("clients-list");

            if (clients.length > 0) {
                clientList.innerHTML = "Clients - <b>" + clients
                    .map(clients => `${clients.name}`)
                    .join(", ") + "</b> (you can select) would like to make some changes in their appointments. Avaulable chat options:";
            } else {
                clientList.innerHTML = "No client in DB available.";
            }
        })
        .catch(error => console.error('Error loading clients:', error));
}

function fetchServices() {
    fetch('/services')
        .then(response => response.json())
        .then(services => {
            const servicesList = document.getElementById("services-list");
            servicesList.innerHTML = "";

            services.forEach(service => {
                const li = document.createElement("li");
                li.textContent = `${service.name} (${service.duration} min)`;
                servicesList.appendChild(li);
            });
        })
        .catch(error => console.error("❌ Error loading services:", error));
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



const modal = document.getElementById("readme-modal");
const readMeBtn = document.getElementById("readMe");
const closeModal = document.getElementById("closeModal");

readMeBtn.addEventListener("click", () => {
    modal.style.display = "flex";
});

closeModal.addEventListener("click", () => {
    modal.style.display = "none";
});

window.addEventListener("click", (event) => {
    if (event.target === modal) {
        modal.style.display = "none";
    }
}); 



document.getElementById("open-time-modal").addEventListener("click", function () {
    document.getElementById("time-modal").style.display = "flex";
});

function closeTimeModal() {
    document.getElementById("time-modal").style.display = "none";
}

window.addEventListener("click", function (event) {
    if (event.target === document.getElementById("time-modal")) {
        closeTimeModal();
    }
});

