(() => {
  "use strict";

  const root = document.documentElement;
  const themeButton = document.querySelector("[data-theme-toggle]");
  const menuButton = document.querySelector("[data-menu-toggle]");
  const nav = document.querySelector("[data-nav]");
  const header = document.querySelector("[data-header]");
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const heroVideo = document.querySelector("[data-hero-video]");
  const hero = heroVideo?.closest(".hero");

  let storedTheme = null;
  try {
    storedTheme = localStorage.getItem("nabtiq-theme");
  } catch {
    storedTheme = null;
  }
  const preferredTheme = matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  const initialTheme = storedTheme === "light" || storedTheme === "dark" ? storedTheme : preferredTheme;

  function applyTheme(theme) {
    root.dataset.theme = theme;
    if (themeButton) themeButton.setAttribute("aria-pressed", String(theme === "dark"));
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      "content",
      theme === "dark" ? "#071621" : "#edf4f2"
    );
  }

  applyTheme(initialTheme);
  themeButton?.addEventListener("click", () => {
    const theme = root.dataset.theme === "dark" ? "light" : "dark";
    try {
      localStorage.setItem("nabtiq-theme", theme);
    } catch {
      // The selected theme still applies for this page when storage is unavailable.
    }
    applyTheme(theme);
  });

  function syncHeroVideo() {
    if (!heroVideo || !hero) return;
    if (reduceMotion.matches) {
      heroVideo.pause();
      hero.removeAttribute("data-video-ready");
      return;
    }
    const revealVideo = () => hero.setAttribute("data-video-ready", "");
    if (heroVideo.readyState >= 2) revealVideo();
    else heroVideo.addEventListener("loadeddata", revealVideo, { once: true });
    const play = heroVideo.play();
    if (play && typeof play.catch === "function") {
      play.catch(() => hero.removeAttribute("data-video-ready"));
    }
  }

  syncHeroVideo();
  if (typeof reduceMotion.addEventListener === "function") {
    reduceMotion.addEventListener("change", syncHeroVideo);
  }

  function closeMenu() {
    menuButton?.setAttribute("aria-expanded", "false");
    nav?.removeAttribute("data-open");
  }

  menuButton?.addEventListener("click", () => {
    const open = menuButton.getAttribute("aria-expanded") !== "true";
    menuButton.setAttribute("aria-expanded", String(open));
    nav?.toggleAttribute("data-open", open);
  });
  nav?.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMenu));
  addEventListener("resize", () => {
    if (innerWidth > 840) closeMenu();
  }, { passive: true });

  const revealItems = [...document.querySelectorAll("[data-reveal]")];
  if (reduceMotion.matches || !("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-visible"));
  } else {
    revealItems
      .filter((item) => item.getBoundingClientRect().top < innerHeight * 1.05)
      .forEach((item) => item.classList.add("is-visible"));
    document.body.dataset.motionReady = "true";
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      }
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    revealItems.filter((item) => !item.classList.contains("is-visible")).forEach((item) => observer.observe(item));
  }

  let frame = 0;
  addEventListener("pointermove", (event) => {
    if (reduceMotion.matches || event.pointerType === "touch") return;
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      root.style.setProperty("--pointer-x", `${event.clientX}px`);
      root.style.setProperty("--pointer-y", `${event.clientY}px`);
    });
  }, { passive: true });

  let lastScroll = 0;
  addEventListener("scroll", () => {
    const current = scrollY;
    header?.toggleAttribute("data-compact", current > 32);
    header?.toggleAttribute("data-hidden", current > lastScroll && current > 220);
    lastScroll = Math.max(0, current);
  }, { passive: true });
})();
