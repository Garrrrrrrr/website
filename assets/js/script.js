
// Rate limiting constants
const RATE_LIMIT = {
  maxSubmissions: 2,
  timeWindow: 5 * 60 * 1000 // 5 minutes in milliseconds
};

// Check if rate limit is exceeded
function isRateLimited() {
  const submissions = JSON.parse(localStorage.getItem('formSubmissions') || '[]');
  const now = Date.now();
  
  // Remove submissions older than 5 minutes
  const recentSubmissions = submissions.filter(time => now - time < RATE_LIMIT.timeWindow);
  
  // Update localStorage
  localStorage.setItem('formSubmissions', JSON.stringify(recentSubmissions));
  
  // Check if limit exceeded
  if (recentSubmissions.length >= RATE_LIMIT.maxSubmissions) {
    const oldestSubmission = recentSubmissions[0];
    const timeUntilReset = Math.ceil((RATE_LIMIT.timeWindow - (now - oldestSubmission)) / 1000);
    return {
      limited: true,
      timeUntilReset
    };
  }
  
  return { limited: false };
}

// Record a submission
function recordSubmission() {
  const submissions = JSON.parse(localStorage.getItem('formSubmissions') || '[]');
  submissions.push(Date.now());
  localStorage.setItem('formSubmissions', JSON.stringify(submissions));
}

// Handle form submission with rate limiting
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  
  if (!form) {
    console.error('Form not found');
    return;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Check rate limit
    const rateLimitCheck = isRateLimited();
    if (rateLimitCheck.limited) {
      alert(`Too many submissions. Please try again in ${rateLimitCheck.timeUntilReset} seconds.`);
      return;
    }

    // Get form data
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const messageInput = document.getElementById('message');
    const button = form.querySelector('button');
    const originalText = button.textContent;

    // Validate form inputs
    if (!nameInput.value.trim() || !emailInput.value.trim() || !messageInput.value.trim()) {
      alert('Please fill in all fields');
      return;
    }

    // Show loading state
    button.textContent = 'Sending...';
    button.disabled = true;

    try {
      // Send form data to FormSubmit in background
      const formData = new FormData(form);
      
      const response = await fetch('https://formsubmit.co/g.tse8888@gmail.com', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        console.log('Email sent successfully!');
        recordSubmission();
        alert('Message sent successfully!');
        form.reset();
        button.textContent = originalText;
        button.disabled = false;
      } else {
        throw new Error('Form submission failed');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message. Please try again later.');
      button.textContent = originalText;
      button.disabled = false;
    }
  });
});
