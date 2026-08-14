document.documentElement.classList.add("js");

const status = document.querySelector("[data-copy-status]");
let statusTimer;

async function copyText(text) {
  await navigator.clipboard.writeText(text);
  if (!status) return;
  status.hidden = false;
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => {
    status.hidden = true;
  }, 1800);
}

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      await copyText(button.dataset.copy || "");
    } catch {
      if (status) {
        status.textContent = document.documentElement.lang.startsWith("zh")
          ? "复制失败"
          : "Copy failed";
        status.hidden = false;
      }
    }
  });
});

const modeCards = [...document.querySelectorAll("[data-mode]")];
const modeNote = document.querySelector("[data-mode-note]");
const modeDescriptions = {
  vector: {
    zh: "当前选择：vector。默认保留 PowerPoint 原生 PDF 中的文字、路径和绘图对象。",
    en: "Selected: vector. This default keeps text, paths, and drawing objects from PowerPoint's native PDF.",
  },
  compatible: {
    zh: "当前选择：compatible。PowerPoint 先渲染高分辨率 TIFF，再生成兼容性更强的图片 PDF。",
    en: "Selected: compatible. PowerPoint renders high-resolution TIFF first, then creates a compatibility-focused image PDF.",
  },
};

modeCards.forEach((card) => {
  card.addEventListener("click", () => {
    modeCards.forEach((item) => item.setAttribute("aria-pressed", String(item === card)));
    if (modeNote) {
      const language = document.documentElement.lang.startsWith("zh") ? "zh" : "en";
      modeNote.textContent = modeDescriptions[card.dataset.mode][language];
    }
  });
});
