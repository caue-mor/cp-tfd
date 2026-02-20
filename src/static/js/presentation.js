// Cupido - Slideshow presentation viewer

document.addEventListener('DOMContentLoaded', () => {
    const totalSlides = parseInt(document.getElementById('total-slides').value);
    const progressBar = document.getElementById('progress-bar');
    const dots = document.querySelectorAll('.nav-dot');
    let current = 0;
    let autoPlayTimer = null;
    const AUTO_PLAY_DELAY = 5000;

    function showSlide(index) {
        // Hide all
        document.querySelectorAll('.slide, .slide-title').forEach(el => {
            el.classList.remove('active');
        });
        // Show target
        const target = document.querySelector(`[data-index="${index}"]`);
        if (target) target.classList.add('active');

        // Update dots
        dots.forEach(dot => dot.classList.remove('active'));
        if (dots[index]) dots[index].classList.add('active');

        // Update progress bar
        const progress = ((index + 1) / totalSlides) * 100;
        progressBar.style.width = progress + '%';

        current = index;
    }

    function next() {
        const nextIndex = (current + 1) % totalSlides;
        showSlide(nextIndex);
    }

    function prev() {
        const prevIndex = (current - 1 + totalSlides) % totalSlides;
        showSlide(prevIndex);
    }

    function startAutoPlay() {
        stopAutoPlay();
        autoPlayTimer = setInterval(next, AUTO_PLAY_DELAY);
    }

    function stopAutoPlay() {
        if (autoPlayTimer) {
            clearInterval(autoPlayTimer);
            autoPlayTimer = null;
        }
    }

    // Navigation buttons
    document.getElementById('next-btn').addEventListener('click', () => {
        next();
        startAutoPlay(); // Reset timer
    });

    document.getElementById('prev-btn').addEventListener('click', () => {
        prev();
        startAutoPlay();
    });

    // Dot navigation
    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            showSlide(parseInt(dot.dataset.index));
            startAutoPlay();
        });
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === ' ') {
            next();
            startAutoPlay();
        } else if (e.key === 'ArrowLeft') {
            prev();
            startAutoPlay();
        }
    });

    // Touch/swipe support
    let touchStartX = 0;
    const slideshow = document.getElementById('slideshow');

    slideshow.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
    }, { passive: true });

    slideshow.addEventListener('touchend', (e) => {
        const diff = touchStartX - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 50) {
            if (diff > 0) next();
            else prev();
            startAutoPlay();
        }
    }, { passive: true });

    // Start auto-play
    startAutoPlay();
});
