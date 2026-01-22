// Starfield Background (Simplified for Auth)
const canvas = document.getElementById('starfield');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const stars = Array(100).fill().map(() => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    size: Math.random() * 2,
    speed: Math.random() * 0.5 + 0.1
}));

function animate() {
    ctx.fillStyle = '#050b14';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#fff';
    stars.forEach(star => {
        star.y += star.speed;
        if (star.y > canvas.height) star.y = 0;
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fill();
    });
    requestAnimationFrame(animate);
}
animate();

// Register Logic
const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : '/api';
const form = document.getElementById('register-form');
const errorMsg = document.getElementById('error-msg');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMsg.style.display = 'none';

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const fullName = document.getElementById('fullname').value;
    const organization = document.getElementById('organization').value;

    try {
        const res = await fetch(`${apiBase}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                password,
                full_name: fullName,
                organization
            })
        });

        const data = await res.json();

        if (res.ok && data.access_token) {
            localStorage.setItem('token', data.access_token);
            window.location.href = 'index.html';
        } else {
            errorMsg.textContent = data.detail || 'Registration Failed';
            errorMsg.style.display = 'block';
        }
    } catch (err) {
        errorMsg.textContent = 'Connection Failure';
        errorMsg.style.display = 'block';
    }
});
