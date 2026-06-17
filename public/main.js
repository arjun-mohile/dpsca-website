// Mobile nav, sticky-header scroll state, and gentle scroll-reveal animations.
// Layout reads/writes are batched into requestAnimationFrame to avoid forced reflows.
(function () {
  // Mobile nav toggle
  var btn = document.querySelector(".nav-toggle");
  var nav = document.querySelector("nav.main");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Header scroll state — rAF-throttled; only writes the class when it actually changes.
  var header = document.querySelector("header.site");
  if (header) {
    var scrolled = false, ticking = false;
    var update = function () {
      ticking = false;
      var s = window.scrollY > 12;
      if (s !== scrolled) { scrolled = s; header.classList.toggle("scrolled", s); }
    };
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    requestAnimationFrame(update);
  }

  // Scroll-reveal — deferred to after first paint so the class writes don't force a
  // synchronous reflow during load. Skipped if the user prefers reduced motion.
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce && "IntersectionObserver" in window) {
    requestAnimationFrame(function () {
      var targets = document.querySelectorAll(".card, .tile, .stat, .step, .metric, .reveal");
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
        });
      }, { threshold: 0.12 });
      targets.forEach(function (el) { el.classList.add("pre-reveal"); io.observe(el); });
    });
  }
})();
