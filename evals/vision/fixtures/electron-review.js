"use strict";

document.querySelector("#reveal").addEventListener("click", () => {
  document.querySelector("#cover").hidden = true;
  document.querySelector("#status").textContent = "Control revealed";
});
