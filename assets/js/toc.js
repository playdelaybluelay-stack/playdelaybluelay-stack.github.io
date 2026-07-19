(function () {
  var desktop = document.querySelector(".toc-desktop");
  if (!desktop || !("IntersectionObserver" in window)) return;
  var links = desktop.querySelectorAll(".linemap a");
  var map = new Map();
  links.forEach(function (a) {
    var h = document.getElementById(a.getAttribute("href").slice(1));
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
})();
