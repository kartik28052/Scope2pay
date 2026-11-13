
const API_URL = "http://127.0.0.1:8000";

// ==========================================
// 1. LOAD ALL PROJECTS
// ==========================================

async function loadDashboard() {
    try {
        const [projectsResponse, quotationsResponse, paymentsResponse] =
            await Promise.all([
                fetch(`${API_URL}/projects`),
                fetch(`${API_URL}/quotations`),
                fetch(`${API_URL}/payments`)
            ]);

        if (!projectsResponse.ok || !quotationsResponse.ok || !paymentsResponse.ok) {
            throw new Error("Failed to fetch dashboard data");
        }

        const projects = await projectsResponse.json();
        const quotations = await quotationsResponse.json();
        const payments = await paymentsResponse.json();

        const paid = payments
            .filter(payment => payment.status === "Paid")
            .reduce((sum, payment) => sum + Number(payment.amount), 0);

        const pending = payments
            .filter(payment => payment.status === "Pending")
            .reduce((sum, payment) => sum + Number(payment.amount), 0);

        document.getElementById("totalProjects").textContent = projects.length;
        document.getElementById("totalQuotations").textContent = quotations.length;

        document.getElementById("dashboardPending").textContent =
            `₹${pending.toLocaleString("en-IN")}`;

        document.getElementById("dashboardRevenue").textContent =
            `₹${paid.toLocaleString("en-IN")}`;

        const container = document.getElementById("dashboardProjects");
        container.replaceChildren();

        const recentProjects = projects.slice(-3).reverse();

        if (recentProjects.length === 0) {
            container.textContent = "No projects created yet.";
            return;
        }

        recentProjects.forEach(project => {
            const card = document.createElement("div");
            card.className = "project-item";

            const heading = document.createElement("h3");
            heading.textContent = project.project_name;

            const details = document.createElement("p");
            details.textContent =
                `Client: ${project.client_name} | Status: ${project.status}`;

            card.append(heading, details);
            container.appendChild(card);
        });

    } catch (error) {
        console.error("Dashboard error:", error);
        document.getElementById("dashboardProjects").textContent =
            "Unable to load dashboard data.";
    }
}

async function loadProjects() {
    const projectList = document.getElementById("projectList");

    try {
        const response = await fetch(`${API_URL}/projects`);

        if (!response.ok) {
            throw new Error("Failed to fetch projects");
        }

        const projects = await response.json();

        if (projects.length === 0) {
            projectList.innerHTML = "<p>No projects found.</p>";
            return;
        }

        projectList.innerHTML = projects.map(project => `
            <div class="project-item">
                <h3>${project.project_name}</h3>
                <p>Client: ${project.client_name}</p>
                <p>${project.description || "No description"}</p>
                <p>Status: ${project.status}</p>
            </div>
        `).join("");

    } catch (error) {
        projectList.innerHTML =
            "<p>Unable to load projects. Please try again.</p>";
        console.error("Project Loading Error:", error);
    }
}


// ==========================================
// 2. CREATE PROJECT
// ==========================================

document.getElementById("projectForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const projectData = {
        client_name: document.getElementById("clientName").value,
        project_name: document.getElementById("projectName").value,
        description: document.getElementById("description").value
    };

    try {
        const response = await fetch(`${API_URL}/projects`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(projectData)
        });

        if (!response.ok) {
            throw new Error("Project creation failed");
        }

        alert("Project created successfully!");

        this.reset();
        await loadProjects();

    } catch (error) {
        console.error(error);
        alert("Unable to create project.");
    }
});


// ==========================================
// 3. SIDEBAR NAVIGATION
// ==========================================

document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", function(event) {
        event.preventDefault();

        const targetPage = this.dataset.page;

        document.querySelectorAll(".page").forEach(page => {
            page.classList.remove("active");
        });

        document.querySelectorAll(".nav-link").forEach(nav => {
            nav.classList.remove("active");
        });

        const selectedPage = document.getElementById(targetPage);

        if (selectedPage) {
            selectedPage.classList.add("active");
            this.classList.add("active");

            if (targetPage === "projects") {
                loadProjects();
            }

            if (targetPage === "quotations") {
                loadQuotations();
            }
            if (targetPage === "dashboard") {
    loadDashboard();
}
        }
    });
});


// ==========================================
// 4. AI CLIENT BRIEF ANALYZER
// ==========================================

document.getElementById("analyzeButton").addEventListener("click", async function() {

    const brief = document.getElementById("clientBrief").value.trim();

    if (!brief) {
        alert("Please enter a client brief first.");
        return;
    }

    this.disabled = true;
    this.textContent = "Analyzing...";

    try {
        const response = await fetch(`${API_URL}/analyze-brief`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                description: brief
            })
        });

        if (!response.ok) {
            throw new Error("Analysis failed: " + response.status);
        }

        const data = await response.json();

        document.getElementById("projectType").textContent =
            data.project_type;

        function populateList(elementId, items) {
            const list = document.getElementById(elementId);
            list.replaceChildren();

            items.forEach(item => {
                const li = document.createElement("li");
                li.textContent = item;
                list.appendChild(li);
            });
        }

        populateList("requirementsList", data.requirements);
        populateList("missingInfoList", data.missing_information);
        populateList("questionsList", data.clarification_questions);

    } catch (error) {
        console.error(error);
        alert("Unable to analyze brief. Check the browser console.");
    } finally {
        this.disabled = false;
        this.textContent = "Analyze Brief";
    }
});


// ==========================================
// 5. LOAD ALL SAVED QUOTATIONS
// ==========================================

async function loadQuotations() {

    const quotationList = document.getElementById("quotationList");

    try {
        const response = await fetch(`${API_URL}/quotations`);

        if (!response.ok) {
            throw new Error("Failed to load quotations");
        }

        const quotations = await response.json();

        quotationList.replaceChildren();

        if (quotations.length === 0) {
            quotationList.textContent = "No quotations found.";
            return;
        }

        quotations.forEach(quotation => {

            const card = document.createElement("div");
            card.className = "project-item";

            const heading = document.createElement("h3");
            heading.textContent = `Quotation #${quotation.id}`;

            const details = document.createElement("p");
            details.textContent =
                `Project ID: ${quotation.project_id} | Price: ₹${quotation.price}`;

            const timeline = document.createElement("p");
            timeline.textContent =
                `Timeline: ${quotation.timeline}`;

            const deliverables = document.createElement("p");
            deliverables.textContent =
                `Deliverables: ${quotation.deliverables}`;

            const status = document.createElement("p");
            status.textContent =
                `Status: ${quotation.status}`;

            card.append(
                heading,
                details,
                timeline,
                deliverables,
                status
            );

            quotationList.appendChild(card);
        });

    } catch (error) {
        console.error("Quotation Loading Error:", error);
        quotationList.textContent = "Unable to load quotations.";
    }
}


// ==========================================
// 6. CREATE QUOTATION
// ==========================================

document.getElementById("quotationForm").addEventListener("submit", async function(event) {

    event.preventDefault();

    const projectId = document.getElementById("quotationProjectId").value;

    const quotationData = {
        deliverables: document.getElementById("deliverables").value,
        timeline: document.getElementById("timeline").value,
        exclusions: document.getElementById("exclusions").value,
        revision_limit: Number(document.getElementById("revisionLimit").value),
        price: Number(document.getElementById("quotationPrice").value)
    };

    const button = this.querySelector("button");

    button.disabled = true;
    button.textContent = "Creating...";

    try {

        const response = await fetch(
            `${API_URL}/projects/${projectId}/quotations`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(quotationData)
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(JSON.stringify(data));
        }

        await loadQuotations();

        alert("Quotation created successfully!");

        this.reset();

    } catch (error) {

        console.error("Quotation Error:", error);

        alert("Unable to create quotation: " + error.message);

    } finally {

        button.disabled = false;
        button.textContent = "Create Quotation";

    }
});


// ==========================================
// 7. INITIAL DATA LOADING
// ==========================================

loadProjects();
loadQuotations();
loadPaymentQuotations();
loadPayments();
loadPaymentProgress();
loadDashboard();

// Load quotations into the payment dropdown
async function loadPaymentQuotations() {
    try {
        const response = await fetch(`${API_URL}/quotations`);
        const quotations = await response.json();

        const dropdown = document.getElementById("paymentQuotation");
        dropdown.innerHTML = '<option value="">Select a quotation</option>';

        quotations.forEach(quotation => {
            const option = document.createElement("option");
            option.value = quotation.id;
            option.textContent =
                `Quotation #${quotation.id} — ₹${quotation.price}`;
            dropdown.appendChild(option);
        });

    } catch (error) {
        console.error("Error loading quotations:", error);
    }
}


// Load payment history
async function loadPayments() {
    try {
        const response = await fetch(`${API_URL}/payments`);
        const payments = await response.json();
        const total = payments.reduce(
    (sum, payment) => sum + Number(payment.amount), 0
);

const paid = payments
    .filter(payment => payment.status === "Paid")
    .reduce((sum, payment) => sum + Number(payment.amount), 0);

const pending = payments
    .filter(payment => payment.status === "Pending")
    .reduce((sum, payment) => sum + Number(payment.amount), 0);

document.getElementById("totalPayments").textContent =
    `₹${total.toLocaleString("en-IN")}`;

document.getElementById("paidAmount").textContent =
    `₹${paid.toLocaleString("en-IN")}`;

document.getElementById("pendingAmount").textContent =
    `₹${pending.toLocaleString("en-IN")}`;

        const paymentList = document.getElementById("paymentList");
        paymentList.innerHTML = "";

        if (payments.length === 0) {
            paymentList.textContent = "No payments recorded yet.";
            return;
        }

        payments.forEach(payment => {
            const card = document.createElement("div");
            card.className = "project-item";

            const heading = document.createElement("h3");
            heading.textContent = `Payment #${payment.id}`;

            const details = document.createElement("p");

details.textContent =
    `Client: ${payment.client_name} | Project: ${payment.project_name}`;

const quotationInfo = document.createElement("p");

quotationInfo.textContent =
    `Quotation: #${payment.quotation_id} | Amount: ₹${payment.amount} | Method: ${payment.payment_method}`;

            const status = document.createElement("p");
            status.textContent = `Status: ${payment.status}`;

            const paidButton = document.createElement("button");
paidButton.textContent = "Mark as Paid";

paidButton.addEventListener("click", async () => {
    await updatePaymentStatus(payment.id, "Paid");
});

card.append(
    heading,
    details,
    quotationInfo,
    status,
    paidButton
);
paymentList.appendChild(card);
        });

    } catch (error) {
        console.error("Error loading payments:", error);
    }
}



// Submit a new payment record
document.getElementById("paymentForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const quotationId = Number(
        document.getElementById("paymentQuotation").value
    );

    const amount = Number(
        document.getElementById("paymentAmount").value
    );

    const paymentMethod = document.getElementById("paymentMethod").value;

    if (!quotationId || !amount || amount <= 0) {
        alert("Please select a quotation and enter a valid amount.");
        return;
    }

    // PayPal checkout
    if (paymentMethod === "PayPal") {
        const message = document.getElementById("paypalMessage");

        try {
            message.textContent = "Creating PayPal checkout...";

            const returnUrl = window.location.origin +
    `/index.html?paypal=success&quotation_id=${quotationId}`;

const cancelUrl = window.location.origin +
    `/index.html?paypal=cancelled&quotation_id=${quotationId}`;

            const response = await fetch(
                `${API_URL}/paypal/create-order/${quotationId}?return_url=${encodeURIComponent(returnUrl)}&cancel_url=${encodeURIComponent(cancelUrl)}`,
                { method: "POST" }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "PayPal order creation failed.");
            }

            window.location.href = data.approval_url;

        } catch (error) {
            message.textContent = error.message;
            console.error("PayPal Error:", error);
        }

        return;
    }

    // Existing manual, bank and UPI payment flow
    const paymentData = {
        quotation_id: quotationId,
        amount: amount,
        payment_method: paymentMethod
    };

    try {
        const response = await fetch(`${API_URL}/payments`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(paymentData)
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.detail || "Unable to record payment.");
            return;
        }

        alert("Payment record created successfully!");

        this.reset();

        await loadPayments();
        await loadPaymentProgress();

    } catch (error) {
        console.error("Payment error:", error);
        alert("Could not connect to the backend.");
    }
});


async function updatePaymentStatus(paymentId, newStatus) {
    try {
        const response = await fetch(
            `${API_URL}/payments/${paymentId}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    status: newStatus
                })
            }
        );

        const result = await response.json();

        if (!response.ok) {
            alert(result.detail || "Could not update payment.");
            return;
        }

        alert("Payment status updated!");
        await loadPayments();
        await loadPaymentProgress();

    } catch (error) {
        console.error(error);
        alert("Backend connection failed.");
    }
}


async function loadPaymentProgress() {
    try {
        const response = await fetch(`${API_URL}/payment-progress`);
        const progressData = await response.json();

        const container = document.getElementById("paymentProgress");
        container.innerHTML = "";

        if (progressData.length === 0) {
            container.textContent = "No quotation data available.";
            return;
        }

        progressData.forEach(item => {
            const card = document.createElement("div");
            card.className = "project-item";

            const heading = document.createElement("h3");
            heading.textContent =
                `Quotation #${item.quotation_id} — ${item.project_name}`;

            const client = document.createElement("p");
            client.textContent = `Client: ${item.client_name}`;

            const total = document.createElement("p");
            total.textContent =
                `Quotation Total: ₹${item.quotation_total}`;

            const paid = document.createElement("p");
            paid.textContent = `Paid: ₹${item.paid_amount}`;

            const pending = document.createElement("p");
            pending.textContent = `Pending: ₹${item.pending_amount}`;

            const remaining = document.createElement("p");
            remaining.textContent =
                `Remaining Balance: ₹${item.remaining_balance}`;

            const percentage = document.createElement("p");
            percentage.textContent =
                `Payment Completed: ${item.progress_percentage}%`;

            const progressBar = document.createElement("progress");
            progressBar.max = 100;
            progressBar.value = Math.min(
                100,
                Math.max(0, item.progress_percentage)
            );

            card.append(
                heading, client, total, paid,
                pending, remaining, percentage, progressBar
            );

            container.appendChild(card);
        });

    } catch (error) {
        console.error("Payment progress error:", error);
    }
}


async function startPayPalCheckout() {
    const quotationId = document.getElementById("paypalQuotationId").value;
    const message = document.getElementById("paypalMessage");

    if (!quotationId || Number(quotationId) <= 0) {
        message.textContent = "Please enter a valid quotation ID.";
        return;
    }

    message.textContent = "Creating PayPal checkout...";

    try {
        const returnUrl = window.location.origin + "/index.html?paypal=success";
        const cancelUrl = window.location.origin + "/index.html?paypal=cancelled";

        const response = await fetch(
            `${API_URL}/paypal/create-order/${quotationId}?return_url=${encodeURIComponent(returnUrl)}&cancel_url=${encodeURIComponent(cancelUrl)}`,
            { method: "POST" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to create PayPal order.");
        }

        message.textContent = "Redirecting to PayPal Sandbox...";

        window.location.href = data.approval_url;

    } catch (error) {
        message.textContent = error.message;
    }
}


async function handlePayPalReturn() {
    const params = new URLSearchParams(window.location.search);

    if (params.get("paypal") === "success") {
        alert("PayPal approval received. Payment capture still needs to be completed.");
    }

    if (params.get("paypal") === "cancelled") {
        alert("PayPal checkout was cancelled.");
    }
}

handlePayPalReturn();
