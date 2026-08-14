document.documentElement.classList.add("js");

const status = document.querySelector("[data-copy-status]");
let statusTimer;

async function copyText(text, button) {
  await navigator.clipboard.writeText(text);
  const copiedLabel = button?.dataset.copiedLabel;
  const originalLabel = button?.dataset.copyLabel || button?.textContent;
  if (button && copiedLabel) button.textContent = copiedLabel;
  if (status) {
    status.textContent = copiedLabel || (document.documentElement.lang.startsWith("zh") ? "已复制" : "Copied");
    status.hidden = false;
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => {
      status.hidden = true;
      if (button && originalLabel) button.textContent = originalLabel;
    }, 2200);
  }
}

document.querySelectorAll("[data-copy], [data-copy-target]").forEach((button) => {
  button.addEventListener("click", async () => {
    const target = button.dataset.copyTarget ? document.getElementById(button.dataset.copyTarget) : null;
    const text = button.dataset.copy || target?.textContent || "";
    try {
      await copyText(text.trim(), button);
    } catch {
      if (status) {
        status.textContent = document.documentElement.lang.startsWith("zh") ? "复制失败" : "Copy failed";
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

fetch("https://api.github.com/repos/Lijinzh/pptx2pdfcrop", { headers: { Accept: "application/vnd.github+json" } })
  .then((response) => response.ok ? response.json() : Promise.reject(new Error("GitHub API unavailable")))
  .then((repository) => {
    document.querySelectorAll("[data-star-count]").forEach((node) => {
      node.textContent = new Intl.NumberFormat().format(repository.stargazers_count);
    });
  })
  .catch(() => {});
