document.addEventListener('DOMContentLoaded', () => {
    const splash = document.getElementById('splash');
    const app = document.getElementById('app');
    const algorithmSelect = document.getElementById('algorithm');
    const codeEditor = document.getElementById('code');
    const inputData = document.getElementById('input-data');
    const inputGroup = document.querySelector('.input-field');
    const autoBtn = document.getElementById('auto-btn');
    const manualBtn = document.getElementById('manual-btn');
    const runBtn = document.getElementById('run-btn');
    const tabs = document.querySelectorAll('.tab');
    const tabPanels = document.querySelectorAll('.tab-panel');
    const aiResult = document.getElementById('ai-result');
    const statusText = document.getElementById('status-text');
    const complexityBadge = document.getElementById('complexity-badge');
    const resizer = document.getElementById('resizer');
    const leftPane = document.querySelector('.left-pane');
    const rightPane = document.querySelector('.right-pane');

    let isManualMode = false;
    let codemirrorEditor = null;
    let chartInstance = null;

    // CodeMirror
    codemirrorEditor = CodeMirror.fromTextArea(document.getElementById('code'), {
        mode: 'python',
        theme: 'dracula',
        lineNumbers: true,
        indentUnit: 4,
        lineWrapping: true
    });
    codemirrorEditor.setSize('100%', '100%');

    // Algorithm templates
    const algorithmTemplates = {
        'custom': '',
        'array-index-access': 'def get_element(arr, index):\n    """Access element at given index"""\n    return arr[index]\n',
        'linear-search': 'def linear_search(arr, target):\n    """Linear search for target"""\n    for i, val in enumerate(arr):\n        if val == target:\n            return i\n    return -1\n',
        'binary-search': 'def binary_search(arr, target=None, left=0, right=None):\n    if target is None:\n        target = len(arr) // 2\n    if right is None:\n        right = len(arr) - 1\n    if left > right:\n        return -1\n    mid = (left + right) // 2\n    if arr[mid] == target:\n        return mid\n    elif arr[mid] < target:\n        return binary_search(arr, target, mid + 1, right)\n    else:\n        return binary_search(arr, target, left, mid - 1)\n',
        'merge-sort': 'def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] < right[j]:\n            result.append(left[i]); i += 1\n        else:\n            result.append(right[j]); j += 1\n    return result + left[i:] + right[j:]\n',
        'bubble-sort': 'def bubble_sort(arr):\n    """Bubble sort algorithm"""\n    n = len(arr)\n    for i in range(n):\n        for j in range(n - i - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr\n',
        'matrix-mult': 'def matrix_mult(A, B):\n    """Naive matrix multiplication"""\n    rows_A = len(A)\n    cols_A = len(A[0])\n    cols_B = len(B[0])\n    result = [[0] * cols_B for _ in range(rows_A)]\n    for i in range(rows_A):\n        for j in range(cols_B):\n            for k in range(cols_A):\n                result[i][j] += A[i][k] * B[k][j]\n    return result\n',
        'fibonacci': 'def fibonacci(n):\n    """Recursive Fibonacci"""\n    if n <= 1:\n        return n\n    return fibonacci(n - 1) + fibonacci(n - 2)\n'
    };

    // Load initial - custom (empty)
    codemirrorEditor.setValue('');

    // Algorithm change
    algorithmSelect.addEventListener('change', () => {
        const alg = algorithmSelect.value;
        if (algorithmTemplates[alg]) {
            codemirrorEditor.setValue(algorithmTemplates[alg]);
        }
    });

    // Mode toggle
    autoBtn.addEventListener('click', () => {
        isManualMode = false;
        autoBtn.classList.add('active');
        manualBtn.classList.remove('active');
        inputGroup.classList.add('hidden');
    });

    manualBtn.addEventListener('click', () => {
        isManualMode = true;
        manualBtn.classList.add('active');
        autoBtn.classList.remove('active');
        inputGroup.classList.remove('hidden');
    });

    // Complexity description labels
    const complexityDescriptions = {
        'O(1)': 'Constant — result found without iterating',
        'O(log n)': 'Logarithmic — input halved each step',
        'O(n)': 'Linear — single pass through input',
        'O(n log n)': 'Linearithmic — divide and conquer',
        'O(n²)': 'Quadratic — nested loop pattern detected',
        'O(n³)': 'Cubic — triple nested loop detected',
        'O(2ⁿ)': 'Exponential — recursive branching without memoization'
    };

    // Render analysis tab with full details
    function renderAnalysis(result) {
        const content = document.getElementById('analysis-content');
        
        // Section 1: Detected Complexity
        const section1 = document.createElement('div');
        section1.className = 'analysis-section';
        section1.innerHTML = `
            <div class="section-label-sm">Detected Complexity</div>
            <div class="complexity-hero">${result.measured}</div>
            <div class="complexity-subtitle">${complexityDescriptions[result.measured] || 'Unknown complexity class'}</div>
            <div class="confidence-bar-wrap">
                <span>Confidence</span>
                <div class="confidence-bar-track">
                    <div class="confidence-bar-fill" style="width: ${result.confidence}%"></div>
                </div>
                <span>${result.confidence}%</span>
            </div>
        `;
        
        // Section 2: Candidate Classes
        const section2 = document.createElement('div');
        section2.className = 'analysis-section';
        let candidatesHtml = '<div class="section-label-sm">Candidate Classes</div>';
        const topCandidates = result.ranking.slice(0, 5);
        const maxConfidence = Math.max(...topCandidates.map(c => c.confidence));
        topCandidates.forEach((candidate, idx) => {
            const isWinner = idx === 0;
            const fillClass = isWinner ? 'winner' : 'other';
            const percent = candidate.confidence;
            candidatesHtml += `
                <div class="candidate-row">
                    <div class="candidate-label">${candidate.label}</div>
                    <div class="candidate-track">
                        <div class="candidate-fill ${fillClass}" style="width: ${percent}%"></div>
                    </div>
                    <div class="candidate-pct">${percent}%</div>
                </div>
            `;
        });
        section2.innerHTML = candidatesHtml;
        
        // Section 3: Runtime Chart
        const section3 = document.createElement('div');
        section3.className = 'analysis-section';
        section3.innerHTML = `
            <div class="section-label-sm">Runtime Across Input Sizes</div>
            <canvas id="complexity-chart" style="max-height: 300px;"></canvas>
        `;
        
        // Section 4: Case Summary
        const section4 = document.createElement('div');
        section4.className = 'analysis-section';
        section4.innerHTML = `
            <div class="case-summary">
                <div class="case-card">
                    <div class="case-card-label">BEST</div>
                    <div class="case-card-value">${result.measured}</div>
                </div>
                <div class="case-card">
                    <div class="case-card-label">AVG</div>
                    <div class="case-card-value">${result.measured}</div>
                </div>
                <div class="case-card">
                    <div class="case-card-label">WORST</div>
                    <div class="case-card-value">${result.measured}</div>
                </div>
            </div>
        `;
        
        content.innerHTML = '';
        content.appendChild(section1);
        content.appendChild(section2);
        content.appendChild(section3);
        content.appendChild(section4);
        
        // Render the chart
        setTimeout(() => renderChart(result.sizes, result.times_best, result.times_avg, result.times_worst, result.measured, result.ranking), 0);
    }

    // Render AI Agent tab
    function renderAIAgent(explanation) {
        const output = document.getElementById('ai-agent-output');
        output.textContent = explanation;
    }

    // Render three-line chart for best/avg/worst
    function renderChart(sizes, timesBest, timesAvg, timesWorst, label, ranking) {
        const canvas = document.getElementById('complexity-chart');
        if (!canvas) return;
        if (chartInstance) { chartInstance.destroy(); chartInstance = null; }

        chartInstance = new Chart(canvas, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Best Case (ms)',
                        data: sizes.map((n, i) => ({ x: n, y: timesBest[i] })),
                        borderColor: '#22c55e',
                        backgroundColor: 'transparent',
                        pointRadius: 4,
                        pointBackgroundColor: '#22c55e',
                        tension: 0.35,
                        fill: false,
                    },
                    {
                        label: 'Average Case (ms)',
                        data: sizes.map((n, i) => ({ x: n, y: timesAvg[i] })),
                        borderColor: '#f4b841',
                        backgroundColor: 'transparent',
                        pointRadius: 4,
                        pointBackgroundColor: '#f4b841',
                        tension: 0.35,
                        fill: false,
                    },
                    {
                        label: 'Worst Case (ms)',
                        data: sizes.map((n, i) => ({ x: n, y: timesWorst[i] })),
                        borderColor: '#ef4444',
                        backgroundColor: 'transparent',
                        pointRadius: 4,
                        pointBackgroundColor: '#ef4444',
                        tension: 0.35,
                        fill: false,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                parsing: false,
                plugins: {
                    legend: {
                        labels: { 
                            color: '#c7b48b', 
                            font: { family: 'JetBrains Mono', size: 11 },
                            padding: 15
                        }
                    },
                    filler: { propagate: false }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: { display: true, text: 'Input size (n)', color: '#7c7468' },
                        ticks: { color: '#7c7468' },
                        grid: { color: 'rgba(255,255,255,0.04)' }
                    },
                    y: {
                        title: { display: true, text: 'Time (ms)', color: '#7c7468' },
                        ticks: { color: '#7c7468' },
                        grid: { color: 'rgba(255,255,255,0.04)' }
                    }
                }
            }
        });
    }

    // Tabs
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            tabPanels.forEach(panel => {
                panel.classList.toggle('active', panel.id === targetTab);
            });
        });
    });

    // Run
    runBtn.addEventListener('click', async () => {
        const algorithm = algorithmSelect.value;
        const code = codemirrorEditor.getValue();
        const input = inputData.value;

        runBtn.innerHTML = '<span class="spinner"></span> Running...';
        runBtn.disabled = true;

        try {
            const result = await eel.run_algorithm(algorithm, code, input)();
            
            if (result.error) {
                // Show error in Analysis tab
                const content = document.getElementById('analysis-content');
                content.innerHTML = `
                    <div style="padding: 40px 20px; text-align: center;">
                        <div style="font-size: 20px; color: #ef4444; font-weight: bold; margin-bottom: 12px;">Error</div>
                        <div style="color: #c7b48b; font-family: 'JetBrains Mono';">${result.error}</div>
                    </div>
                `;
                document.querySelector('[data-tab="analysis"]').click();
                statusText.textContent = `Error: ${result.error}`;
                complexityBadge.textContent = 'ERR';
            } else {
                // Update badge and status
                complexityBadge.textContent = result.measured;
                statusText.textContent = `Detected: ${result.measured} (${Math.round(result.confidence)}%) — Static predicted: ${result.static}`;
                
                // Render Analysis tab
                renderAnalysis(result);
                document.querySelector('[data-tab="analysis"]').click();
                
                // Render AI Agent tab in background
                renderAIAgent(result.explanation);
            }
        } catch (error) {
            const content = document.getElementById('analysis-content');
            content.innerHTML = `
                <div style="padding: 40px 20px; text-align: center;">
                    <div style="font-size: 20px; color: #ef4444; font-weight: bold; margin-bottom: 12px;">Error</div>
                    <div style="color: #c7b48b; font-family: 'JetBrains Mono';">${error.message}</div>
                </div>
            `;
            statusText.textContent = 'Error';
            complexityBadge.textContent = 'ERR';
        } finally {
            runBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M4 2.5v11l9-5.5-9-5.5z"/></svg> Run';
            runBtn.disabled = false;
        }
    });

    const quitBtn = document.getElementById('quit-btn');
    if (quitBtn) {
        quitBtn.addEventListener('click', () => {
            try {
                window.close();
            } catch (error) {
                console.warn('Quit request failed', error);
            }
            app.classList.add('hidden');
            statusText.textContent = 'Quit';
        });
    }

    // Resizer - drag to resize panes
    let isResizing = false;
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const container = document.querySelector('.split-pane');
        const containerRect = container.getBoundingClientRect();
        let newWidth = e.clientX - containerRect.left;
        newWidth = Math.max(300, Math.min(newWidth, containerRect.width - 400));
        leftPane.style.width = newWidth + 'px';
    });

    document.addEventListener('mouseup', () => {
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    });

    // Splash
    setTimeout(() => {
        splash.classList.add('fade-out');
        app.classList.remove('hidden');
        codemirrorEditor.refresh();
        setTimeout(() => splash.remove(), 500);
    }, 2000);
});