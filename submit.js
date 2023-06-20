document.getElementById('appointmentForm').addEventListener('submit', function(event) {
    event.preventDefault();
    var formData = new FormData(this);
    var jsonData = {};
    for (var [key, value] of formData) {
      jsonData[key] = value;
    }
    fetch('/book', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(jsonData)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      window.location.href = '/appointments';  // Redirect to the thank you page
    })
    .catch((error) => {
      console.error('Error:', error);
    });
  });
  