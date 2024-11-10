const switchToRegisterBtn = document.getElementById('switchToRegisterBtn');
const switchToLoginBtn = document.getElementById('switchToLoginBtn');
const loginForm = document.getElementById('loginForm');
const registrationSection = document.getElementById('registrationSection');

switchToRegisterBtn.addEventListener('click', function() {
  loginForm.style.display = 'none';
  registrationSection.style.display = 'block';
});

switchToLoginBtn.addEventListener('click', function() {
  registrationSection.style.display = 'none';
  loginForm.style.display = 'block';
});

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
  
  function setRoleCookie(role) {
    document.cookie = `userRole=${role}; path=/;`;
  }
  
  function displayRegistrationSection() {
    const role = getCookie('userRole');
    const registrationSection = document.getElementById('registrationSection');
    const adminOption = document.getElementById('adminOption');
  
    if (role === 'admin') {
      registrationSection.style.display = 'block';
      adminOption.style.display = 'none'; 
    } else if (role === 'owner') {
      registrationSection.style.display = 'block';
      adminOption.style.display = 'inline-block'; 
    } else {
      registrationSection.style.display = 'none';
    }
  }
  
  document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();
  
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
  
    try {
      const response = await fetch('/api/authorization/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
  
      if (response.ok) {
        setRoleCookie(data.role);
        alert('Login successful!');
        displayRegistrationSection();
      } else {
        alert(`Login failed: ${data.message}`);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Error logging in. Please try again.');
    }
  });
  
  document.getElementById('registerForm').addEventListener('submit', async function(event) {
    event.preventDefault();
  
    const newUsername = document.getElementById('newUsername').value;
    const newPassword = document.getElementById('newPassword').value;
    const role = document.querySelector('input[name="role"]:checked').value;
  
    try {
      const response = await fetch('/api/authorization/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: newUsername, password: newPassword, role })
      });
      
      const data = await response.json();
  
      if (response.ok) {
        alert('User registered successfully!');
        document.getElementById('registerForm').reset();
      } else {
        alert(`Registration failed: ${data.message}`);
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert('Error registering user. Please try again.');
    }
  });
  