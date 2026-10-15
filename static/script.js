
const supportForm = document.getElementById("supportForm");
const messageInput = document.getElementById("message");
const submitBtn = document.getElementById("submitBtn");

const resultPanel = document.getElementById("resultPanel");
const statusText = document.getElementById("statusText");
const resultOutput = document.getElementById("resultOutput");
const reviewActions = document.getElementById("reviewActions");
const errorMessage = document.getElementById("errorMessage");

const approveBtn = document.getElementById("approveBtn");
const rejectBtn = document.getElementById("rejectBtn");

let currentThreadId = null;

function showResult(data) {
    resultPanel.hidden = false;
    statusText.textContent = `Status: ${data.status || "unknown"}`;
    resultOutput.textContent = JSON.stringify(data, null, 2);

    reviewActions.hidden = data.status !== "awaiting_approval";
}

async function sendRequest(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : JSON.stringify(data.detail || data)
        );
    }

    return data;
}

supportForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = messageInput.value.trim();

    if (!message) {
        errorMessage.textContent = "Please describe your issue.";
        return;
    }

    submitBtn.disabled = true;
    errorMessage.textContent = "";
    resultPanel.hidden = true;
    reviewActions.hidden = true;

    currentThreadId = crypto.randomUUID();

    try {
        const data = await sendRequest("/support", {
            thread_id: currentThreadId,
            message: message
        });

        showResult(data);
    } catch (error) {
        errorMessage.textContent = error.message;
    } finally {
        submitBtn.disabled = false;
    }
});

async function submitReview(approved) {
    if (!currentThreadId) {
        errorMessage.textContent = "Submit a request first.";
        return;
    }

    approveBtn.disabled = true;
    rejectBtn.disabled = true;
    errorMessage.textContent = "";

    try {
        const data = await sendRequest(
            `/review/${encodeURIComponent(currentThreadId)}`,
            { approved: approved }
        );

        showResult(data);
    } catch (error) {
        errorMessage.textContent = error.message;
    } finally {
        approveBtn.disabled = false;
        rejectBtn.disabled = false;
    }
}

approveBtn.addEventListener("click", () => submitReview(true));
rejectBtn.addEventListener("click", () => submitReview(false));
