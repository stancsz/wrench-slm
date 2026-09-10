const fallback = {
  snapshot_ran_at: "2026-09-10T00:00:00-06:00",
  project_state: "weight_release_ready",
  checkpoint_released: true,
  model_release: {
    version: "V21",
    status: "WEIGHTS READY FOR RELEASE",
    adapter_sha256: "6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348",
    frozen_holdout: { exact: "440/440", routine: "280/280", fallback: "160/160" },
    context_suite: { exact: "220/220", routine: "140/140", fallback: "80/80" }
  },
  milestones: {
    M1_training_contract: { verdict: "PASS" },
    M2_training_run: { verdict: "PASS" },
    M3_frozen_holdout: { verdict: "PASS" },
    M4_context_generalization: { verdict: "PASS" },
    M5_package_verification: { verdict: "PASS" },
    M6_router_serving: { verdict: "HOLD" }
  }
};

const dateLabel = (iso) => new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));

function setText(selector, value) {
  const element = document.querySelector(selector);
  if (element) element.textContent = value;
}

function renderStatus(data) {
  const release = data.model_release || {};
  const holdout = release.frozen_holdout || {};
  const context = release.context_suite || {};
  setText("[data-stat=holdout]", holdout.exact || "not recorded");
  setText("[data-stat=context]", context.exact || "not recorded");
  setText("[data-stat=checkpoint]", data.checkpoint_released ? "V21 ready" : "deferred");
  setText("[data-stat=release-status]", release.status || "not recorded");
  setText("[data-stat=adapter]", release.adapter_sha256 ? `${release.adapter_sha256.slice(0, 12)}…` : "not recorded");
  setText("[data-stat=sample-date]", dateLabel(data.snapshot_ran_at));

  document.querySelectorAll("[data-milestone]").forEach((element) => {
    const milestone = data.milestones?.[element.dataset.milestone];
    if (!milestone) return;
    const verdict = milestone.verdict.toLowerCase();
    element.dataset.verdict = verdict;
    element.querySelector("[data-verdict]")?.replaceChildren(document.createTextNode(milestone.verdict));
    const dot = element.querySelector(".dot");
    const badge = element.querySelector(".badge");
    if (dot) dot.className = `dot ${verdict === "hold" ? "hold" : verdict === "pass" ? "pass" : "fail"}`;
    if (badge) badge.className = `badge ${verdict === "hold" ? "hold" : verdict === "pass" ? "pass" : "fail"}`;
  });
}

async function init() {
  let data = fallback;
  try {
    const response = await fetch("assets/status.json", { cache: "no-store" });
    if (response.ok) data = await response.json();
  } catch (error) {
    document.documentElement.dataset.offline = "true";
  }
  renderStatus(data);
  document.querySelectorAll("[data-year]").forEach((element) => element.textContent = new Date().getFullYear());
  if (window.IntersectionObserver) {
    const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add("is-visible");
    }), { threshold: .12 });
    document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
  }
}

document.addEventListener("DOMContentLoaded", init);
