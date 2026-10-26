import type { Resume } from "./types";

// ─── DOM refs ────────────────────────────────────────────────────────────────
const log = document.getElementById("log") as HTMLDivElement;
const input = document.getElementById("msg-input") as HTMLInputElement;
const sendBtn = document.getElementById("send-btn") as HTMLButtonElement;
const fileInput = document.getElementById("file-input") as HTMLInputElement;
const attachBtn = document.getElementById("attach-btn") as HTMLButtonElement;
const resumeBadge = document.getElementById("resume-badge") as HTMLSpanElement;

// ─── API ─────────────────────────────────────────────────────────────────────
async function apiParse(res: Response): Promise<unknown> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((data as Record<string, string>).error ?? `Error ${res.status}`);
  return data;
}

async function uploadResume(file: File): Promise<Resume> {
  const fd = new FormData();
  fd.append("file", file);
  const data = await apiParse(await fetch("/api/upload/", { method: "POST", body: fd }));
  return (data as { resume: Resume }).resume;
}

interface AgentResult {
  reply: string;
  type: "text" | "jobs" | "applications" | "roles";
  jobs?: JobData[] | null;
  applications?: AppData[] | null;
}

interface JobData {
  display_id: number;
  job_id: number;
  title: string;
  company: string;
  location: string;
  experience_required: string | number;
  remote: boolean;
  skills: string[];
  description_snippet: string;
  match_reason: string;
  source_link: string;
}

interface AppData {
  index: number;
  title: string;
  company: string;
  status: string;
  date: string;
}

async function sendChat(message: string): Promise<AgentResult> {
  const data = await apiParse(
    await fetch("/api/chat/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    })
  );
  return data as AgentResult;
}

// ─── Rendering helpers ────────────────────────────────────────────────────────
function esc(s: string): string {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function scrollBottom(): void {
  log.scrollTop = log.scrollHeight;
}

function addBubble(role: "user" | "bot", content: string | HTMLElement): HTMLDivElement {
  const d = document.createElement("div");
  if (role === "user") {
    d.className = "flex justify-end";
    const inner = document.createElement("div");
    inner.className = "max-w-xl bg-neutral-100 text-neutral-950 font-normal text-sm px-4 py-2.5 rounded-lg border border-neutral-300 shadow-sm";
    if (typeof content === "string") {
      inner.innerHTML = content;
    } else {
      inner.appendChild(content);
    }
    d.appendChild(inner);
  } else {
    d.className = "flex justify-start w-full";
    const inner = document.createElement("div");
    inner.className = "max-w-2xl w-full bg-neutral-950 text-neutral-200 text-sm p-4 rounded-lg border border-neutral-800 leading-relaxed";
    if (typeof content === "string") {
      inner.innerHTML = content;
    } else {
      inner.className = "w-full";
      inner.appendChild(content);
    }
    d.appendChild(inner);
  }
  log.appendChild(d);
  scrollBottom();
  return d;
}

function thinkingEl(): HTMLDivElement {
  const d = document.createElement("div");
  d.className = "flex justify-start w-full";
  d.innerHTML = `
    <div class="bg-neutral-950 border border-neutral-800 rounded-lg px-4 py-3 flex items-center gap-1.5">
      <span class="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-pulse"></span>
      <span class="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-pulse delay-100"></span>
      <span class="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-pulse delay-200"></span>
      <span class="text-xs text-neutral-400 font-mono ml-2 uppercase tracking-widest">Thinking</span>
    </div>
  `;
  log.appendChild(d);
  scrollBottom();
  return d;
}

/** Format plain text: bold **x**, line breaks, no raw markdown underscores */
function formatText(text: string): string {
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong class='text-white font-semibold'>$1</strong>")
    .replace(/\n/g, "<br>");
}

// ─── Resume Card ──────────────────────────────────────────────────────────────
function renderResumeCard(r: Resume): HTMLDivElement {
  const initials = (r.name || "?")
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const skills = (r.skills || [])
    .map(
      (s: string) =>
        `<span class="text-xs px-2 py-0.5 rounded border border-neutral-700 bg-neutral-900 text-neutral-300 font-mono">${esc(s)}</span>`
    )
    .join("");

  const exp_list = Array.isArray(r.experience)
    ? (r.experience as string[]).map((e: string) => `<li class="text-neutral-400 text-xs">${esc(e)}</li>`).join("")
    : "";
  const edu_list = (r.education || []).map((e: string) => `<li class="text-neutral-400 text-xs">${esc(e)}</li>`).join("");
  const proj_list = (r.projects || []).map((p: string) => `<li class="text-neutral-400 text-xs">${esc(p)}</li>`).join("");

  const card = document.createElement("div");
  card.className = "border border-neutral-800 bg-neutral-950 rounded-lg p-5 space-y-4 w-full";
  card.innerHTML = `
    <div class="flex items-center gap-3 pb-3 border-b border-neutral-800">
      <div class="w-10 h-10 rounded bg-white text-black font-bold flex items-center justify-center text-sm uppercase">
        ${initials}
      </div>
      <div>
        <div class="text-base font-semibold text-white tracking-tight">${esc(r.name || "Candidate Resume")}</div>
        <div class="text-xs text-neutral-400">${esc(r.designation || "Applicant")}</div>
      </div>
    </div>

    <div class="space-y-3 text-xs">
      ${
        r.email || r.phone
          ? `
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Contact</span>
        <span class="text-neutral-300">${esc(r.email || "")}${r.email && r.phone ? " · " : ""}${esc(r.phone || "")}</span>
      </div>`
          : ""
      }
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Experience</span>
        <span class="text-neutral-300">${r.experience_years} year(s)</span>
      </div>
      ${
        skills
          ? `
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Skills</span>
        <div class="flex flex-wrap gap-1.5 flex-1">${skills}</div>
      </div>`
          : ""
      }
      ${
        exp_list
          ? `
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Work</span>
        <ul class="list-disc list-inside space-y-1 flex-1">${exp_list}</ul>
      </div>`
          : ""
      }
      ${
        edu_list
          ? `
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Education</span>
        <ul class="list-disc list-inside space-y-1 flex-1">${edu_list}</ul>
      </div>`
          : ""
      }
      ${
        proj_list
          ? `
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Projects</span>
        <ul class="list-disc list-inside space-y-1 flex-1">${proj_list}</ul>
      </div>`
          : ""
      }
    </div>

    <div class="pt-3 border-t border-neutral-800 text-[11px] text-neutral-400 font-mono uppercase tracking-wider">
      Resume parsed successfully. Ask me to find matching jobs or suggest roles.
    </div>
  `;
  return card;
}

// ─── Job Cards ────────────────────────────────────────────────────────────────
function renderJobCard(job: JobData): HTMLDivElement {
  const card = document.createElement("div");
  card.className = "border border-neutral-800 bg-neutral-950 rounded-lg overflow-hidden transition-all duration-150 hover:border-neutral-600";

  const remoteBadge = job.remote
    ? `<span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded border border-neutral-700 bg-neutral-900 text-neutral-300">Remote</span>`
    : "";
  const expBadge = job.experience_required
    ? `<span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded border border-neutral-800 bg-black text-neutral-400">${esc(String(job.experience_required))}</span>`
    : "";
  const skills = (job.skills || [])
    .slice(0, 8)
    .map(
      (s: string) =>
        `<span class="text-xs px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-neutral-300 font-mono">${esc(s)}</span>`
    )
    .join("");
  const desc = job.description_snippet
    ? `<div class="space-y-1">
        <div class="text-[11px] uppercase tracking-wider text-neutral-500 font-medium">Description</div>
        <div class="text-xs text-neutral-300 leading-relaxed">${esc(job.description_snippet)}…</div>
       </div>`
    : "";

  card.innerHTML = `
    <div class="jc-summary p-4 flex items-start justify-between cursor-pointer select-none bg-neutral-950 hover:bg-neutral-900/50 transition-colors">
      <div class="space-y-1">
        <div class="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">Job ${job.display_id}</div>
        <div class="text-sm font-semibold text-white tracking-tight">${esc(job.title)}</div>
        <div class="text-xs text-neutral-400 font-normal">${esc(job.company)} · ${esc(job.location)}</div>
        <div class="flex items-center gap-1.5 pt-1">
          ${remoteBadge}
          ${expBadge}
        </div>
      </div>
      <div class="jc-chevron text-neutral-400 text-sm font-mono transition-transform duration-200">
        &#8595;
      </div>
    </div>
    <div class="jc-body hidden border-t border-neutral-800 p-4 space-y-4 bg-black">
      ${desc}
      ${
        skills
          ? `<div class="space-y-1.5">
        <div class="text-[11px] uppercase tracking-wider text-neutral-500 font-medium">Required Skills</div>
        <div class="flex flex-wrap gap-1">${skills}</div>
      </div>`
          : ""
      }
      <div class="flex items-center gap-2 pt-2 border-t border-neutral-900">
        ${
          job.source_link
            ? `<button class="jc-link-btn px-3 py-1.5 bg-white text-black hover:bg-neutral-200 text-xs font-semibold rounded uppercase tracking-wider transition-colors cursor-pointer" data-link="${esc(job.source_link)}">Apply on site</button>`
            : ""
        }
        <button class="jc-apply-btn px-3 py-1.5 border border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-neutral-200 text-xs font-semibold rounded uppercase tracking-wider transition-colors cursor-pointer" data-apply="${job.display_id}">Mark as applied</button>
      </div>
    </div>
  `;

  // Toggle expand
  const summary = card.querySelector(".jc-summary") as HTMLDivElement;
  const body = card.querySelector(".jc-body") as HTMLDivElement;
  const chevron = card.querySelector(".jc-chevron") as HTMLDivElement;

  summary.addEventListener("click", () => {
    const isHidden = body.classList.contains("hidden");
    if (isHidden) {
      body.classList.remove("hidden");
      chevron.innerHTML = "&#8593;";
    } else {
      body.classList.add("hidden");
      chevron.innerHTML = "&#8595;";
    }
    scrollBottom();
  });

  // Apply on site button → open source link
  card.querySelectorAll<HTMLButtonElement>("[data-link]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      window.open(btn.dataset.link!, "_blank", "noopener");
    });
  });

  // Mark as applied → send chat command
  card.querySelectorAll<HTMLButtonElement>("[data-apply]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = btn.dataset.apply!;
      ask(`apply to ${id}`, true);
      btn.textContent = "Applied";
      btn.disabled = true;
      btn.classList.add("opacity-50", "cursor-not-allowed");
    });
  });

  return card;
}

function renderJobs(jobs: JobData[], header: string): HTMLDivElement {
  const wrapper = document.createElement("div");
  wrapper.className = "space-y-3 w-full";
  wrapper.innerHTML = `<div class="text-xs font-mono uppercase tracking-wider text-neutral-400 border-b border-neutral-800 pb-2">${esc(header)}</div>`;
  jobs.forEach((j) => wrapper.appendChild(renderJobCard(j)));
  return wrapper;
}

// ─── Applications Table ───────────────────────────────────────────────────────
function renderApplications(apps: AppData[], header: string): HTMLDivElement {
  const rows = apps
    .map(
      (a) => `
    <tr class="border-b border-neutral-800/60 hover:bg-neutral-900/40 text-xs">
      <td class="p-3 text-neutral-500 font-mono">${a.index}</td>
      <td class="p-3"><strong class="text-white">${esc(a.title)}</strong><br><span class="text-neutral-400 text-[11px]">${esc(a.company)}</span></td>
      <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-mono border border-neutral-700 bg-neutral-900 text-neutral-300 uppercase">${esc(a.status)}</span></td>
      <td class="p-3 text-neutral-400 font-mono text-[11px]">${esc(a.date)}</td>
    </tr>`
    )
    .join("");

  const wrapper = document.createElement("div");
  wrapper.className = "w-full space-y-3 border border-neutral-800 rounded-lg p-4 bg-neutral-950";
  wrapper.innerHTML = `
    <div class="text-xs font-mono uppercase tracking-wider text-neutral-400 border-b border-neutral-800 pb-2">${esc(header)}</div>
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-neutral-800 text-[11px] uppercase tracking-wider text-neutral-500">
            <th class="p-3 font-semibold">#</th>
            <th class="p-3 font-semibold">Position</th>
            <th class="p-3 font-semibold">Status</th>
            <th class="p-3 font-semibold">Date</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
  return wrapper;
}

// ─── Main chat handler ────────────────────────────────────────────────────────
let isBusy = false;

async function ask(text: string, showUser = true): Promise<void> {
  if (isBusy) return;
  isBusy = true;
  sendBtn.disabled = true;

  if (showUser) addBubble("user", esc(text));
  const thinking = thinkingEl();

  try {
    const result = await sendChat(text);

    // Replace thinking bubble
    thinking.remove();

    // Show text reply (always)
    if (result.reply) {
      addBubble("bot", formatText(result.reply));
    }

    // Render structured data
    if (result.type === "jobs" && result.jobs && result.jobs.length > 0) {
      const wrapper = renderJobs(result.jobs, `${result.jobs.length} matching jobs`);
      addBubble("bot", wrapper);
    } else if (result.type === "applications" && result.applications) {
      const wrapper = renderApplications(
        result.applications,
        `${result.applications.length} application(s)`
      );
      addBubble("bot", wrapper);
    }
  } catch (e) {
    thinking.remove();
    addBubble("bot", `<span class="text-neutral-400 font-mono">${esc((e as Error).message)}</span>`);
  } finally {
    isBusy = false;
    sendBtn.disabled = false;
    scrollBottom();
  }
}

// ─── Events ───────────────────────────────────────────────────────────────────
sendBtn.addEventListener("click", () => {
  const text = input.value.trim();
  if (!text || isBusy) return;
  input.value = "";
  ask(text);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    sendBtn.click();
  }
});

attachBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", async () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  fileInput.value = "";

  addBubble("user", `Uploaded resume: ${esc(file.name)}`);
  const thinking = thinkingEl();

  try {
    const resume = await uploadResume(file);

    // Show parsed resume card — do NOT auto-search
    thinking.remove();
    const card = renderResumeCard(resume);
    addBubble("bot", card);

    // Show resume badge in header
    resumeBadge.classList.remove("hidden");
    resumeBadge.classList.add("inline-block");
  } catch (e) {
    thinking.remove();
    addBubble("bot", `<span class="text-neutral-400 font-mono">Could not parse resume: ${esc((e as Error).message)}</span>`);
  }
});

// ─── Welcome ──────────────────────────────────────────────────────────────────
addBubble(
  "bot",
  "Welcome to Hidani Job Assistant.<br><br>" +
    "Upload your resume using the paperclip icon or ask commands below:<br>" +
    "<strong class='text-white'>Find jobs</strong> — 'Show me frontend developer jobs'<br>" +
    "<strong class='text-white'>Filter</strong> — 'Only remote roles' or 'Jobs needing Python'<br>" +
    "<strong class='text-white'>Suggest roles</strong> — 'What roles can I apply to?'<br>" +
    "<strong class='text-white'>Apply</strong> — 'Apply to jobs 1, 2, 3'<br>" +
    "<strong class='text-white'>Track</strong> — 'Show my applied jobs'"
);
