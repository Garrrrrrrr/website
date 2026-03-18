
emailjs.init('ENgU6BiCfyKVg6j6d'); 

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

// Get form elements
const form = document.querySelector('form');
const nameInput = document.getElementById('name');
const emailInput = document.getElementById('email');
const messageInput = document.getElementById('message');

// Wait for DOM to be ready, then attach event listener
document.addEventListener('DOMContentLoaded', () => {
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

    // Success - record submission before resetting
    recordSubmission();
    alert('Message sent successfully!');
    form.reset();
    button.textContent = originalText;
    button.disabled = false;
  } catch (error) {
    console.error('Error sending email:', error);
    alert('Failed to send message. Please try again later.');
    button.textContent = originalText;
    button.disabled = false;
  }
});
});
