document.querySelectorAll(".codeblock").forEach(function (block) {
  var btn = block.querySelector(".cb-copy");
  var live = block.querySelector(".cb-live");
  if (!btn) return;
  btn.addEventListener("click", function () {
    var code = block.querySelector("pre code") || block.querySelector("pre");
    navigator.clipboard.writeText(code.innerText).then(function () {
      var svg = btn.innerHTML;
      btn.innerHTML =
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
      live.textContent = btn.dataset.copied;
      setTimeout(function () { btn.innerHTML = svg; live.textContent = ""; }, 1200);
    });
  });
});
