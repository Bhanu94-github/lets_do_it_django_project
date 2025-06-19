// Cleaned and formatted script.js with GSAP, modals, and form handlers

document.addEventListener('DOMContentLoaded', () => {
    gsap.registerPlugin(ScrollTrigger);

    // Smooth scrolling
    document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            gsap.to(window, {
                duration: 1.2,
                scrollTo: targetId,
                ease: "power2.inOut"
            });
            if (window.innerWidth <= 768) {
                document.querySelector('nav').classList.remove('active');
            }
        });
    });

    // Hamburger menu
    const hamburger = document.querySelector('.hamburger-menu');
    const nav = document.querySelector('nav');
    if (hamburger) {
        hamburger.addEventListener('click', () => {
            nav.classList.toggle('active');
            hamburger.querySelector('i').classList.toggle('fa-bars');
            hamburger.querySelector('i').classList.toggle('fa-times');
        });
    }

    // Animate sections on scroll
    gsap.utils.toArray('.animate-on-scroll').forEach(el => {
        gsap.fromTo(el, { opacity: 0, y: 100 }, {
            opacity: 1,
            y: 0,
            duration: 1.2,
            ease: "power3.out",
            scrollTrigger: {
                trigger: el,
                start: "top 85%",
                toggleActions: "play none none reverse"
            }
        });
    });

    // 3D hover for AI modules
    document.querySelectorAll('.ai-module').forEach(module => {
        gsap.set(module, { rotationX: 0, rotationY: 0, y: 0, boxShadow: '0 10px 30px rgba(0,0,0,0.08)' });
        const hover = gsap.timeline({ paused: true });
        hover.to(module, {
            rotationX: -5,
            rotationY: 5,
            y: -10,
            boxShadow: '0 15px 40px rgba(0,240,255,0.2)',
            borderColor: 'var(--primary-color)',
            duration: 0.3,
            ease: "power2.out"
        });
        module.addEventListener('mouseenter', () => hover.play());
        module.addEventListener('mouseleave', () => hover.reverse());
    });

    // Modal logic
    const signInBtn = document.getElementById('signInBtn');
    const signUpBtn = document.getElementById('signUpBtn');
    const startGameBtn = document.getElementById('startGameBtn');
    const signInModal = document.getElementById('signInModal');
    const signUpModal = document.getElementById('signUpModal');
    const startGameModal = document.getElementById('startGameModal');
    const gameOverModal = document.getElementById('gameOverModal');
    const closeButtons = document.querySelectorAll('.modal .close-button');

    function openModal(modal) {
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        const focusable = modal.querySelectorAll('input, button');
        if (focusable.length) focusable[0].focus();
    }

    function closeModal(modal) {
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
    }

    // Open modals
    if (signInBtn && signInModal) signInBtn.onclick = e => { e.preventDefault(); openModal(signInModal); };
    if (signUpBtn && signUpModal) signUpBtn.onclick = e => { e.preventDefault(); openModal(signUpModal); };
    if (startGameBtn && startGameModal) startGameBtn.onclick = () => {
        closeModal(startGameModal);
        document.body.style.overflow = 'auto';
    };

    // Close buttons
    closeButtons.forEach(btn => btn.onclick = () => closeModal(btn.closest('.modal')));

    // Click outside modal
    window.onclick = e => { if (e.target.classList.contains('modal')) closeModal(e.target); };

    // Escape key
    window.onkeydown = e => { if (e.key === 'Escape') document.querySelectorAll('.modal.active').forEach(m => closeModal(m)); };

    // Form logic
    const signInForm = document.getElementById("signInForm");
    const signUpForm = document.getElementById("signUpForm");

    if (signInForm) {
        signInForm.onsubmit = e => {
            e.preventDefault();
            const email = document.getElementById("signInEmail").value;
            const password = document.getElementById("signInPassword").value;

            fetch("/students/login/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                if (data.status === "success") {
                    closeModal(signInModal);
                    signInForm.reset();
                    window.location.href = "/students/dashboard/";
                }
            });
        };
    }

    if (signUpForm) {
        signUpForm.onsubmit = e => {
            e.preventDefault();
            const name = document.getElementById("signUpName").value;
            const username = document.getElementById("signUpUsername").value;
            const email = document.getElementById("signUpEmail").value;
            const phone = document.getElementById("signUpPhone").value;
            const password = document.getElementById("signUpPassword").value;
            const confirmPassword = document.getElementById("signUpConfirmPassword").value;

            if (password !== confirmPassword) {
                alert("Passwords do not match.");
                return;
            }

            fetch("/students/register/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, username, phone, email, password })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                if (data.status === "success") {
                    closeModal(signUpModal);
                    signUpForm.reset();
                }
            });
        };
    }

    // Game over scroll detection
    ScrollTrigger.create({
        trigger: "body",
        start: "bottom bottom",
        end: "+=1",
        onEnter: () => openModal(gameOverModal),
        once: true
    });
});