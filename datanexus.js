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
});