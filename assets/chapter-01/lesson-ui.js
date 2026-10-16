// Layout and navigation work independently of the 3D module's CDN loading.
(() => {
  const app = document.getElementById("app");
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  const scroll = document.getElementById("panel-scroll");
  const positions = new Map();
  let active = "controls";
  function openPanel(name, focus = false) {
    if (!tabs.some((tab) => tab.dataset.panel === name)) return;
    if (app.classList.contains("is-focus")) setFocus(false);
    positions.set(active, scroll.scrollTop);
    active = name;
    tabs.forEach((tab) => {
      const selected = tab.dataset.panel === name;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      document.getElementById(tab.getAttribute("aria-controls")).hidden =
        !selected;
      if (selected && focus) tab.focus();
    });
    scroll.scrollTop = positions.get(name) || 0;
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => openPanel(tab.dataset.panel));
    tab.addEventListener("keydown", (event) => {
      let next;
      if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
      if (event.key === "ArrowLeft")
        next = (index + tabs.length - 1) % tabs.length;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = tabs.length - 1;
      if (next !== undefined) {
        event.preventDefault();
        openPanel(tabs[next].dataset.panel, true);
      }
    });
  });
  document.querySelectorAll("[data-open-panel]").forEach((button) => {
    button.addEventListener("click", () =>
      openPanel(button.dataset.openPanel, true),
    );
  });
  const focusButton = document.getElementById("btn-focus");
  function setFocus(expanded) {
    app.classList.toggle("is-focus", expanded);
    focusButton.setAttribute("aria-pressed", String(expanded));
    focusButton.setAttribute(
      "aria-label",
      expanded ? "返回操作面板" : "展开地球视图",
    );
    focusButton.title = expanded ? "返回操作面板" : "展开地球视图";
  }
  focusButton.addEventListener("click", () =>
    setFocus(!app.classList.contains("is-focus")),
  );
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && app.classList.contains("is-focus")) {
      setFocus(false);
      focusButton.focus();
    }
  });
  for (const [attribute, inputId] of [
    ["speed", "speed"],
    ["day", "doy"],
  ]) {
    const input = document.getElementById(inputId);
    const buttons = [...document.querySelectorAll(`[data-${attribute}]`)];
    const update = () =>
      buttons.forEach((button) =>
        button.setAttribute(
          "aria-pressed",
          String(button.dataset[attribute] === input.value),
        ),
      );
    buttons.forEach((button) =>
      button.addEventListener("click", () => {
        input.value = button.dataset[attribute];
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }),
    );
    input.addEventListener("input", update);
  }
  const topic = document.getElementById("kp-select");
  const syncTopic = () => {
    const text = topic.selectedOptions[0].textContent;
    document.getElementById("stage-topic").textContent = text;
    document.getElementById("knowledge-topic").textContent = text;
    document.querySelector(".knowledge-formula").hidden =
      topic.value !== "local-time";
  };
  topic.addEventListener("change", syncTopic);
  syncTopic();
  const loading = document.getElementById("scene-loading");
  const retry = document.getElementById("btn-retry");
  const delayed = window.setTimeout(() => {
    document.getElementById("loading-title").textContent = "地球加载较慢";
    document.getElementById("loading-detail").textContent =
      "请检查网络，或重新加载页面。";
    retry.hidden = false;
  }, 20000);
  window.addEventListener(
    "lesson:ready",
    () => {
      clearTimeout(delayed);
      loading.hidden = true;
      document.getElementById("scene-status").textContent = "实时模拟";
    },
    { once: true },
  );
  window.addEventListener("lesson:texture-error", () => {
    clearTimeout(delayed);
    document.getElementById("loading-title").textContent = "底图未能加载";
    document.getElementById("loading-detail").textContent =
      "请检查网络后重新加载。";
    retry.hidden = false;
  });
  retry.addEventListener("click", () => window.location.reload());
})();
