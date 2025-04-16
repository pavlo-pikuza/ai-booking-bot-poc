document.addEventListener("DOMContentLoaded", function () {
    const clock = document.getElementById("clock");
    const clientSelector = document.querySelector(".client-selector");
    const setTimeBtn = document.getElementById("set-time-btn");

    const readMeModal = document.getElementById("readme-modal");
    const readMeBtn = document.getElementById("readMe");
    const readMeModalClose = document.getElementById("readme-modal-close-btn");

    const timeModal = document.getElementById("time-modal");
    const openTimeModal = document.getElementById("open-time-modal");

    const chatHistory = document.querySelector(".chat-history");
    const messageInput = document.querySelector(".chat-input input")
    const chatSendBtn = document.getElementById("chat-send");
    
    let isRunning = true;    
    let client_id = null
    let timeUpdater = null;
    
    readMeBtn.addEventListener("click", () => {
        readMeModal.style.display = "flex";
    });
    
    readMeModalClose.addEventListener("click", () => {
        readMeModal.style.display = "none";
    });
    
    window.addEventListener("click", (event) => {
        if (event.target === readMeModal) {
            readMeModal.style.display = "none";
        }
    }); 

    window.addEventListener("click", function (event) {
        if (event.target === timeModal) {
            timeModal.style.display = "none";
        }
    });
    
    openTimeModal.addEventListener("click", function () {
        timeModal.style.display = "flex";
    });
        

    clock.addEventListener("click", toggleClock);

    chatSendBtn.addEventListener("click", function () {
        sendMessage();
    });

    clientSelector.addEventListener("change", function () {
        client_id = this.value;
        if (client_id) {
            messageInput.value = "";
            loadChatHistory(client_id);
        }
    });

    setTimeBtn.addEventListener("click", function () {
        const selectedDay = document.getElementById("day-select").value;
        const selectedHour = document.getElementById("hour-input").value;
        const selectedMinute = document.getElementById("minute-input").value;

        fetch("/time", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                action: "set",
                time: `${selectedHour}:${selectedMinute}`,
                day: `${selectedDay}`
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


    /////
    fetch("/time")
        .then(response => response.json())
        .then(data => {
            updateClockAppearance(data.status);
            handleTimeUpdates(isRunning);
        });

    fetchServices()
    fetchClientList()
    fetchClients()

    if (clientSelector.value) {
        loadChatHistory(clientSelector.value);
    }

    //// functions
    function updateTimeAndPlot() {
        fetch("/time")
            .then(response => response.json())
            .then(data => {
                if (!data.time) return;

                const [hours, minutes] = data.time.split(":");
                const day = data.day;

                updatePlot()
                clock.innerHTML = `<div class="clock-time">${hours}<span id="colon">:</span>${minutes}</div><div class="clock-day">${day}</div>`;
                updateClockAppearance(data.status);
            })
            .catch(error => console.error("Error fetching time:", error));
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
    
    function loadChatHistory(clientId) {

        fetch(`/chat_history/${clientId}`)
        .then(response => response.json())
        .then(messages => {
            chatHistory.innerHTML = "";
    
            messages.forEach(msg => {
                addMessageToChat(msg.message, msg.day, msg.time, msg.is_client_sender);
            });
        })
        .catch(error => console.error("Error loading chat history:", error));
    }

    function addMessageToChat(message, day, time, isClientSender = true) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", isClientSender ? "client-message" : "bot-message");

        const dayAbbr = day.slice(0, 3);
        const formattedTime = `${dayAbbr} ${time}`;
    
        messageDiv.innerHTML = `
            <span class="timestamp">${formattedTime}</span>
           ${message}
        `;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // for chat
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
                if (data.length > 0) {
                    client_id = data[0].id;
                    loadChatHistory(client_id);
                }
            })
            .catch(error => console.error("Error loading clients:", error));
    }

    // for Readme form
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

    // for Readme form
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

    function processChat(message) {
        console.log("🧠 Message processing:", message);
    }
    
    function sendMessage() {
        const message = messageInput.value.trim();
    
        if (!message || !client_id) {
            alert(`Please type a message first! Message:"${message}".`);
            return;
        }
    
        fetch("/send_message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ client_id: client_id, message: message, is_client_sender: true })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error:", data.error);
                return;
            }
    
            addMessageToChat(data.message, data.day, data.time, isClientSender = true);
            messageInput.value = "";
            processChat();
        })
        .catch(error => console.error("Error sending message:", error));
    }
});
