document.addEventListener('DOMContentLoaded', () => {
    // Generate QR Code
    const qrcode = new QRCode(document.getElementById("qrcode"), {
        text: window.location.href,
        width: 128,
        height: 128
    });
 
    // Update leaderboard every 2 minutes
    function updateLeaderboard() {
        fetch('http://127.0.0.1:5000/api/leaderboard')  // Update to use the correct backend URL
            .then(response => response.json())
            .then(data => {
                const leaderboardBody = document.getElementById('leaderboard-body');
                leaderboardBody.innerHTML = data.map((team, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${team.name}</td>
                        <td>${team.score}</td>
                    </tr>
                `).join('');
            })
            .catch(error => console.error('Error:', error));
    }
 
    // Initial leaderboard load
    updateLeaderboard();
   
    // Update every 2 minutes
    setInterval(updateLeaderboard, 120000);

    // Add event listener for the form submission
    const submitBtn = document.getElementById('continueBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(event) {
            const teamName = document.getElementById('team-name')?.value;
            const inputText = document.getElementById('inputText')?.value;
            
            if (!teamName || !inputText) {
                alert('Please fill out all required fields.');
                return;
            }
            
            // Get the file path to your songs dataset
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
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Display the results
                    const outputResult = document.getElementById('outputResult');
                    if (outputResult) {
                        outputResult.innerHTML = `
                            <h3>Score: ${data.score}/100</h3>
                            <div class="evaluation-feedback">
                                ${marked.parse(data.feedback)}
                            </div>
                        `;
                    }
                    
                    // Advance to the next step to show results
                    const currentStep = 1;
                    const totalSteps = 2;
                    if (currentStep < totalSteps) {
                        document.querySelectorAll('.step').forEach(el => {
                            el.classList.remove('active');
                        });
                        document.getElementById(`step${currentStep+1}`).classList.add('active');
                        document.getElementById('progress').style.width = `${((currentStep+1) / totalSteps) * 100}%`;
                    }
                    
                    // Update the leaderboard immediately
                    updateLeaderboard();
                } else {
                    alert(`Error: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your submission.');
            });
        });
    }
});