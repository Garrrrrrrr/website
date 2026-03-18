
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

// Wait for DOM and EmailJS to be ready
document.addEventListener('DOMContentLoaded', () => {
  // Check if EmailJS is loaded
  if (typeof emailjs === 'undefined') {
    console.error('EmailJS library not loaded. Check that the CDN script is included.');
    return;
  }

  // Initialize EmailJS
  emailjs.init('ENgU6BiCfyKVg6j6d');
  console.log('EmailJS initialized successfully!');

  // Get form elements
  const form = document.querySelector('form');
  const nameInput = document.getElementById('name');
  const emailInput = document.getElementById('email');
  const messageInput = document.getElementById('message');

  if (!form) {
    console.error('Form not found');
    return;
  }

  // Handle form submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Check rate limit
    const rateLimitCheck = isRateLimited();
    if (rateLimitCheck.limited) {
      alert(`Too many submissions. Please try again in ${rateLimitCheck.timeUntilReset} seconds.`);
      return;
    }

    // Validate form inputs
    if (!nameInput.value.trim() || !emailInput.value.trim() || !messageInput.value.trim()) {
      alert('Please fill in all fields');
      return;
    }

    // Show loading state
    const button = form.querySelector('button');
    const originalText = button.textContent;
    button.textContent = 'Sending...';
    button.disabled = true;

    try {
      // Send email using EmailJS
      console.log('Attempting to send email...');
      
      const response = await emailjs.send(
        'service_d8hif8b', 
        'template_a3wnu0b', 
        {
          from_name: nameInput.value,
          from_email: emailInput.value,
          message: messageInput.value,
          to_email: 'g.tse8888@gmail.com'
        }
      );

      console.log('Email sent successfully!', response);
      recordSubmission();
      alert('Message sent successfully!');
      form.reset();
      button.textContent = originalText;
      button.disabled = false;
    } catch (error) {
      console.error('Error sending email:', error);
      if (error.text) {
        console.error('Error details:', error.text);
      }
      alert('Failed to send message. Check the browser console for details.');
      button.textContent = originalText;
      button.disabled = false;
    }
  });
});
