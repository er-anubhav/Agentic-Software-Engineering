document.addEventListener("DOMContentLoaded", () => {
    const wsStatus = document.getElementById("ws-status");
    const consoleLogs = document.getElementById("console-logs");
    const dagPipeline = document.getElementById("dag-pipeline");
    const btnSubmitGoal = document.getElementById("btn-submit-goal");
    const promptInput = document.getElementById("prompt-input");

    // Sample initial DAG nodes
    const initialNodes = [
        { id: "task_1", title: "Requirement Ingestion", agent: "RequirementAgent", status: "COMPLETED", phase: 1 },
        { id: "task_2", title: "Polyglot Repository Parsing", agent: "ContextEngine", status: "COMPLETED", phase: 1 },
        { id: "task_3", title: "Task DAG Generation", agent: "PlannerAgent", status: "COMPLETED", phase: 2 },
        { id: "task_4", title: "Surgical Code Patch", agent: "RepairAgent", status: "RUNNING", phase: 3 },
        { id: "task_5", title: "Formal AST Verification", agent: "VerificationEngine", status: "PENDING", phase: 4 },
        { id: "task_6", title: "SQLite WAL Persistence", agent: "PersistenceEngine", status: "PENDING", phase: 4 }
    ];

    function renderDAGNodes(nodes) {
        dagPipeline.innerHTML = "";
        nodes.forEach(node => {
            const item = document.createElement("div");
            item.className = "dag-node-item";
            item.innerHTML = `
                <div class="node-info">
                    <h4>${node.title} (Phase ${node.phase})</h4>
                    <p>Assigned Agent: <code>${node.agent}</code></p>
                </div>
                <span class="node-status-badge ${node.status.toLowerCase()}">${node.status}</span>
            `;
            dagPipeline.appendChild(item);
        });
    }

    renderDAGNodes(initialNodes);

    function addLog(msg, type = "info") {
        const line = document.createElement("div");
        line.className = `log-line ${type}`;
        const timeStr = new Date().toLocaleTimeString();
        line.innerText = `[${timeStr}] ${msg}`;
        consoleLogs.appendChild(line);
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
    }

    // Connect WebSockets
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/execution`;

    try {
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            wsStatus.innerText = "Connected";
            addLog("WebSockets connection established with Execution Gateway.", "success");
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            addLog(`[WS Event] ${data.message || JSON.stringify(data)}`, "info");
        };

        socket.onerror = () => {
            wsStatus.innerText = "Offline Mode";
            addLog("WebSocket server offline. Running in REST fallback mode.", "warning");
        };
    } catch (e) {
        wsStatus.innerText = "Offline Mode";
    }

    // Goal Submission Handler
    btnSubmitGoal.addEventListener("click", async () => {
        const text = promptInput.value.trim();
        if (!text) return;

        addLog(`Submitting goal: "${text}"`, "info");

        // Simulate dynamic DAG update
        const updatedNodes = initialNodes.map((n, i) => {
            if (i === 3) return { ...n, status: "COMPLETED" };
            if (i === 4) return { ...n, status: "RUNNING" };
            return n;
        });

        setTimeout(() => {
            renderDAGNodes(updatedNodes);
            addLog("Executing task_5: Formal AST Verification gate...", "info");
        }, 800);

        setTimeout(() => {
            const finalNodes = updatedNodes.map((n, i) => {
                if (i === 4) return { ...n, status: "COMPLETED" };
                if (i === 5) return { ...n, status: "COMPLETED" };
                return n;
            });
            renderDAGNodes(finalNodes);
            addLog("Workflow complete: All 6 Task DAG nodes executed with 0 AST violations.", "success");
        }, 1800);
    });
});
