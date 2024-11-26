document.getElementById('start-scraping').addEventListener('click', () => {
    const url = document.getElementById('scraping-url').value;
    if (!url) {
      alert('Please enter a URL.');
      return;
    }
  
    fetch('/set_scraping_url', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }), // Send the URL as JSON
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert('Scraping URL set successfully!');
        } else {
          alert(`Error: ${data.error}`);
        }
      })
      .catch(err => console.error('Error:', err));
  });
  
  // Make the header clickable to refresh the page and reset fields
document.getElementById('header-title').addEventListener('click', () => {
  // Clear the logs
  const logMessages = document.getElementById('log-messages');
  logMessages.innerHTML = ''; // Clear all log messages
  lastLogLength = 0; // Reset the log length tracker

  // Clear the URL input box
  const urlInput = document.getElementById('scraping-url');
  urlInput.value = ''; // Reset the input value

  // Refresh the page by navigating to the root URL
  window.location.href = '/';
});


  document.getElementById('start-scraping').addEventListener('click', () => {
    const url = document.getElementById('scraping-url').value;
    // Clear the logs when the Start Scraping button is clicked
    const logMessages = document.getElementById('log-messages');
    logMessages.innerHTML = ''; // Clear all log messages
    lastLogLength = 0; // Reset the log length tracker
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
        const progressBar = document.getElementById('progress-bar');
        const progressPercentage = document.getElementById('progress-percentage');
  
        // Update progress bar width and percentage text
        progressBar.style.width = `${status}%`;
        progressPercentage.textContent = `${status}%`;
  
        // If scraping is complete, stop updating
        if (status >= 100) {
          clearInterval(progressInterval);
  
          // Delay the alert and exportButtons display by 3 seconds
          setTimeout(() => {
            alert("Scraping completed!");
            exportButtons.style.display = 'flex';
          }, 3000);
        }
      })
      .catch(err => console.error('Error fetching progress:', err));
  }
  
  // Set interval to periodically fetch progress every 2 seconds
  const progressInterval = setInterval(updateProgressBar, 2000);
  let lastLogLength = 0;
  
  function fetchLogs() {
    fetch('/get-logs')
      .then(response => response.json())
      .then(logs => {
        const logBox = document.getElementById('log-box');
        const logMessages = document.getElementById('log-messages');
  
        // Make the log box visible
        if (logs.length > 0 && logBox.style.display === 'none') {
          logBox.style.display = 'block';
        }
  
        // Append only new messages
        for (let i = lastLogLength; i < logs.length; i++) {
          const newMessage = document.createElement('div');
          newMessage.textContent = logs[i];
          logMessages.appendChild(newMessage);
        }
  
        // Update the last log length
        lastLogLength = logs.length;
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
  
