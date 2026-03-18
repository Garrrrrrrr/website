
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

  form.addEventListener('submit', (e) => {
    // Check rate limit
    const rateLimitCheck = isRateLimited();
    if (rateLimitCheck.limited) {
      e.preventDefault();
      alert(`Too many submissions. Please try again in ${rateLimitCheck.timeUntilReset} seconds.`);
      return;
    }

    // Record submission if not rate limited
    recordSubmission();
    
    // Show loading state
    const button = form.querySelector('button');
    const originalText = button.textContent;
    button.textContent = 'Sending...';
    button.disabled = true;

    // Reset button after delay
    setTimeout(() => {
      button.textContent = originalText;
      button.disabled = false;
    }, 2000);
  });
});
