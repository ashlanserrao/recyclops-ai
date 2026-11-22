// Runs in <head> before first paint, so a dark-mode visitor never sees a white flash.
// A file, not an inline script: the CSP allows scripts from this origin only.
(function () {
  var preference = "auto";
  try {
    preference = localStorage.getItem("recyclops.theme") || "auto";
  } catch (e) {}
  var dark = preference === "dark" ||
    (preference !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
})();
