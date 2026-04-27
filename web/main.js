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
        'merge-sort': 'def merge_sort(arr):\n    """Merge sort algorithm"""\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n',
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
            const result = await eel.run_algorithm(algorithm, code, input);
            
            document.querySelector('[data-tab="ai"]').click();
            aiResult.textContent = result;
            
            // Extract and show complexity
            const match = result.match(/O\([^)]+\)/);
            complexityBadge.textContent = match ? match[0] : 'O(?)';
            statusText.textContent = match ? `Detected: ${match[0]}` : 'Done';
        } catch (error) {
            aiResult.textContent = 'Error: ' + error.message;
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