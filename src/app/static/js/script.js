// SMART FARMING DECISION SUPPORT SYSTEM - Client Side Interaction Scripts

// Sidebar Mobile Toggle
document.addEventListener("DOMContentLoaded", () => {
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const sidebar = document.querySelector(".sidebar");
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("mobile-open");
        });
    }
});

// Language Switcher Toggle
function changeLanguage() {
    const langSelect = document.getElementById("lang-select");
    if (langSelect) {
        const lang = langSelect.value;
        localStorage.setItem("selectedLang", lang);
        
        // Parse current query parameters and update the lang value
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set("lang", lang);
        window.location.href = window.location.pathname + "?" + urlParams.toString();
    }
}

// Align lang select value on DOM load
document.addEventListener("DOMContentLoaded", () => {
    const langSelect = document.getElementById("lang-select");
    if (langSelect) {
        const urlParams = new URLSearchParams(window.location.search);
        const langParam = urlParams.get("lang");
        const savedLang = localStorage.getItem("selectedLang") || "en";
        
        if (langParam) {
            langSelect.value = langParam;
            localStorage.setItem("selectedLang", langParam);
        } else {
            langSelect.value = savedLang;
        }
    }
});

// File input image preview
function previewImage(event) {
    const fileInput = event.target;
    const previewContainer = document.getElementById("preview-container");
    const previewImg = document.getElementById("preview-img");
    
    if (fileInput.files && fileInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (previewImg) {
                previewImg.src = e.target.result;
            }
            if (previewContainer) {
                previewContainer.style.display = "block";
            }
        };
        reader.readAsDataURL(fileInput.files[0]);
    }
}

// Chatbot messages submit handler
async function handleChatSubmit(event) {
    event.preventDefault();
    const inputEl = document.getElementById("chat-input");
    const message = inputEl.value.trim();
    if (!message) return;
    
    const messagesContainer = document.getElementById("chat-messages-container");
    
    // Add user chat bubble
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble user";
    userBubble.innerText = message;
    messagesContainer.appendChild(userBubble);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    inputEl.value = "";
    
    // Add bot typing loading indicator bubble
    const botBubble = document.createElement("div");
    botBubble.className = "chat-bubble bot";
    botBubble.innerText = "...";
    messagesContainer.appendChild(botBubble);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Prepare API request
    const formData = new FormData();
    formData.append("user_message", message);
    const savedLang = localStorage.getItem("selectedLang") || "en";
    formData.append("lang", savedLang);
    
    try {
        const response = await fetch("/chatbot_message", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        botBubble.innerText = data.reply;
    } catch (error) {
        botBubble.innerText = "Error: Could not connect to AI agricultural advisor.";
    }
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
