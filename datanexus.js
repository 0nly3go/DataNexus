document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const card = document.querySelector('.card');
    const progressBar = document.getElementById('progress');
    const continueBtn = document.getElementById('continueBtn');
    const backBtn = document.getElementById('backBtn');
    const copyBtn = document.getElementById('copyBtn');
    const outputResult = document.getElementById('outputResult');
    const leaderboardBody = document.getElementById('leaderboard-body');
    
    // Generate QR Code if element exists
    const qrcodeElement = document.getElementById("qrcode");
    if (qrcodeElement) {
        const qrcode = new QRCode(qrcodeElement, {
            text: window.location.href,
            width: 128,
            height: 128
        });
    }

    // Configure marked.js
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false,
        pedantic: false,
        sanitize: false,
        smartLists: true,
        smartypants: false,
        tables: true
    });

    // Update progress function
    function updateProgress(step, totalSteps = 2) {
        if (progressBar) {
            progressBar.style.width = `${(step / totalSteps) * 100}%`;
        }
    }

    // Show specific step function
    function showStep(stepNumber) {
        document.querySelectorAll('.step').forEach(el => {
            el.classList.remove('active');
        });
        document.getElementById(`step${stepNumber}`).classList.add('active');
        updateProgress(stepNumber);
    }

    // Update leaderboard function
    function updateLeaderboard() {
        if (!leaderboardBody) return;

        fetch('http://127.0.0.1:5000/api/leaderboard')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                leaderboardBody.innerHTML = data.map((team, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${team.name}</td>
                        <td>${team.score}</td>
                    </tr>
                `).join('');
            })
            .catch(error => {
                console.error('Error updating leaderboard:', error);
                if (leaderboardBody) {
                    leaderboardBody.innerHTML = `<tr><td colspan="3">Error loading leaderboard: ${error.message}</td></tr>`;
                }
            });
    }
 
    // Initial leaderboard load
    updateLeaderboard();
   
    // Update every 2 minutes
    setInterval(updateLeaderboard, 120000);

    // Handle submission
    function handleSubmit() {
        const teamName = document.getElementById('team-name')?.value;
        const teamMembers = document.getElementById('team-members')?.value;
        const inputText = document.getElementById('inputText')?.value;
        
        if (!teamName || !teamMembers || !inputText) {
            alert('Please fill out all required fields.');
            return;
        }
        
        // Show loading state and move to step 2
        showStep(2);
        
        if (outputResult) {
            outputResult.innerHTML = `
                <div class="evaluation-loading">
                    <div class="loading-spinner"></div>
                    <p>Evaluating your prompt against songs dataset...</p>
                    <p>This may take up to a minute. Please wait.</p>
                </div>
            `;
        }
        
        // Path to the songs dataset on the server
        const filePath = 'c:\\Users\\josma\\OneDrive\\Desktop\\DataNexus\\backends\\data\\Prompt Engineering Songs.xlsx';
        
        // Call the evaluate-songs API
        fetch('http://127.0.0.1:5000/api/evaluate-songs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                team_name: teamName,
                file_path: filePath,
                prompt: inputText
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Display the results
                const scorePercentage = data.score;
                let scoreColor = '#4CAF50'; // green
                if (scorePercentage < 60) scoreColor = '#f44336'; // red
                else if (scorePercentage < 80) scoreColor = '#ff9800'; // orange
                
                outputResult.innerHTML = `
                    <div class="score-summary">
                        <h3>Score: ${data.score}/100</h3>
                        <div class="score-bar-container">
                            <div class="score-bar" style="width: ${scorePercentage}%; background-color: ${scoreColor}"></div>
                        </div>
                        <p>Correct classifications: ${data.correct}/${data.total}</p>
                    </div>
                    <div class="evaluation-feedback">
                        ${marked.parse(data.feedback)}
                    </div>
                `;
                
                // Update the leaderboard immediately
                updateLeaderboard();
            } else {
                outputResult.innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${data.error || 'Unknown error occurred'}</p>
                        ${data.details ? `<pre>${data.details}</pre>` : ''}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (outputResult) {
                outputResult.innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>An error occurred while processing your submission.</p>
                        <p>Details: ${error.message}</p>
                        <p>Make sure the server is running at http://127.0.0.1:5000/</p>
                    </div>
                `;
            }
        });
    }

    // Add event listeners
    if (continueBtn) {
        continueBtn.addEventListener('click', handleSubmit);
    }
    
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            showStep(1);
        });
    }
    
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const resultText = document.querySelector('.evaluation-feedback')?.innerText;
            if (resultText) {
                navigator.clipboard.writeText(resultText)
                    .then(() => alert('Results copied to clipboard!'))
                    .catch(err => alert('Failed to copy: ' + err));
            } else {
                alert('No results to copy.');
            }
        });
    }

    // Initialize first step
    updateProgress(1);
});