// Dark mode toggle
(function() {
  const toggle = document.getElementById('theme-toggle');
  const icon = toggle.querySelector('i');
  const saved = localStorage.getItem('theme');

  if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.setAttribute('data-theme', 'dark');
    icon.classList.replace('fa-moon', 'fa-sun');
  }

  toggle.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
      document.documentElement.removeAttribute('data-theme');
      icon.classList.replace('fa-sun', 'fa-moon');
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
      icon.classList.replace('fa-moon', 'fa-sun');
      localStorage.setItem('theme', 'dark');
    }
  });
})();

// Rate limiting constants
const RATE_LIMIT = {
  maxSubmissions: 2,
  timeWindow: 5 * 60 * 1000
};

function isRateLimited() {
  const submissions = JSON.parse(localStorage.getItem('formSubmissions') || '[]');
  const now = Date.now();
  const recentSubmissions = submissions.filter(time => now - time < RATE_LIMIT.timeWindow);
  localStorage.setItem('formSubmissions', JSON.stringify(recentSubmissions));

  if (recentSubmissions.length >= RATE_LIMIT.maxSubmissions) {
    const oldestSubmission = recentSubmissions[0];
    const timeUntilReset = Math.ceil((RATE_LIMIT.timeWindow - (now - oldestSubmission)) / 1000);
    return { limited: true, timeUntilReset };
  }
  return { limited: false };
}

function recordSubmission() {
  const submissions = JSON.parse(localStorage.getItem('formSubmissions') || '[]');
  submissions.push(Date.now());
  localStorage.setItem('formSubmissions', JSON.stringify(submissions));
}

// Handle form submission
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('#contactForm');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const rateLimitCheck = isRateLimited();
    if (rateLimitCheck.limited) {
      alert(`Too many submissions. Please try again in ${rateLimitCheck.timeUntilReset} seconds.`);
      return;
    }

    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const messageInput = document.getElementById('message');

    if (!nameInput.value.trim() || !emailInput.value.trim() || !messageInput.value.trim()) {
      alert('Please fill in all fields');
      return;
    }

    const button = form.querySelector('button');
    const originalText = button.textContent;
    button.textContent = 'Sending...';
    button.disabled = true;

    const formData = new FormData();
    formData.append('name', nameInput.value);
    formData.append('email', emailInput.value);
    formData.append('message', messageInput.value);

    fetch('https://formspree.io/f/xqeywjbo', {
      method: 'POST',
      body: formData,
      mode: 'no-cors'
    })
    .then(() => {
      recordSubmission();
      alert('Message sent successfully!');
      form.reset();
    })
    .catch(() => {
      alert('Failed to send message. Please try again later.');
    })
    .finally(() => {
      button.textContent = originalText;
      button.disabled = false;
    });
  });
});