(function () {
  var desktop = document.querySelector(".toc-desktop");
  if (!desktop || !("IntersectionObserver" in window)) return;
  var mq = window.matchMedia("(min-width: 1100px)");
  var started = false;
  function init() {
    if (started) return;
    started = true;
    var links = desktop.querySelectorAll(".linemap a");
    var map = new Map();
    links.forEach(function (a) {
      var id = decodeURIComponent(a.getAttribute("href").slice(1));
      var h = document.getElementById(id);
      if (h) map.set(h, a);
    });
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) current = map.get(e.target);
      });
      if (!current) return;
      var passed = true;
      links.forEach(function (a) {
        a.removeAttribute("aria-current");
        a.parentElement.classList.toggle("passed", passed && a !== current);
        if (a === current) { a.setAttribute("aria-current", "location"); passed = false; }
      });
    }, { rootMargin: "-10% 0px -70% 0px" });
    map.forEach(function (_a, h) { io.observe(h); });
  }
  if (mq.matches) { init(); }
  else {
    mq.addEventListener("change", function handler(e) {
      if (e.matches) { init(); mq.removeEventListener("change", handler); }
    });
  }
})();
