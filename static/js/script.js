
let existingLogs = new Set(); // Store unique logs
let lastLogLength = 0;
const progressBar = document.getElementById('progress-bar');
const progressPercentage = document.getElementById('progress-percentage');
let stageCheck = 0;

// Function to clear logs
function clearLogsAndUrl() {
  const stat = 0;
  existingLogs.clear();
  // Clear the logs
  const logMessages = document.getElementById('log-messages');
  logMessages.innerHTML = ''; // Clear all log messages
  lastLogLength = 0; // Reset the log length tracker
  progressBar.style.width = `${stat}%`;
  progressPercentage.textContent = `${stat}%`;
  let stageCheck = 0;
}
  
  // Make the header clickable to refresh the page and reset fields
document.getElementById('header-title').addEventListener('click', () => {
  clearLogsAndUrl()
  // Clear the URL input box
  const urlInput = document.getElementById('scraping-url');
  urlInput.value = ''; // Reset the input value
  // Refresh the page by navigating to the root URL
  window.location.href = '/';
});


  document.getElementById('start-scraping').addEventListener('click', () => {
    const url = document.getElementById('scraping-url').value;
    clearLogsAndUrl()
    if (!url) {
      alert('Please enter a URL.');
      return;
    }
  
    fetch('/start-scraping', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }),
    })
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          alert(`Error: ${data.error}`);
        } else {
          alert(data.message);
        }
      })
      .catch(err => console.error('Error:', err));
  });
  
function updateProgressBar() {
  exportButtons = document.getElementById("export-buttons");
  fetch('/check_status')
    .then(response => response.json())
    .then(data => {
      const status = data.status; // Assuming this is a percentage (e.g., 45 for 45%)
      

      // Update progress bar width and percentage text
      progressBar.style.width = `${status}%`;
      progressPercentage.textContent = `${status}%`;

      // If scraping is complete, stop updating
      if (status >= 100) {
        clearInterval(progressInterval);
      }
    })
    .catch(err => console.error('Error fetching progress:', err));
}
  
// Set interval to periodically fetch progress every 2 seconds
const progressInterval = setInterval(updateProgressBar, 2000);




function fetchLogs() {
  fetch('/get-logs')
    .then(response => response.json())
    .then(logs => {
      const logBox = document.getElementById('log-box');
      const logMessages = document.getElementById('log-messages');

      // Make the log box visible if logs are available
      if (logs.length > 0 && logBox.style.display === 'none') {
        logBox.style.display = 'block';
      }

      // Append only new messages
      logs.forEach(log => {
        if (!existingLogs.has(log)) { // Check if the log is new
          const newMessage = document.createElement('div');
          newMessage.textContent = log;
          logMessages.appendChild(newMessage);
          existingLogs.add(log); // Add to the set of existing logs
        }

        if (existingLogs.has("Downloading...") && stageCheck == 0) {
          alert("Scraping completed!");
          const exportButtons = document.getElementById('export-buttons');
          exportButtons.style.display = 'flex';
          stageCheck = 1;
        }
      });
    })
    .catch(err => console.error('Error fetching logs:', err));
}

  
function downloadFile(fileType) {
  fetch(`/download-file/${fileType}`)
    .then(response => {
      if (!response.ok) throw new Error(`Failed to download ${fileType} file.`);
      return response.blob();
    })
    .then(blob => {
      // Create a temporary download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${fileType}_file.${fileType}`;
      link.click();
      window.URL.revokeObjectURL(url);
    })
    .catch(err => console.error(err));
}

// Poll the server every 2 seconds
setInterval(fetchLogs, 2000);


  
