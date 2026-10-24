import { uploadResume, sendChat } from "./api";
import type { Resume } from "./types";

const $ = <T extends HTMLElement>(id: string) =>
  document.getElementById(id) as T;
const log = $<HTMLDivElement>("log");
const input = $<HTMLInputElement>("msg");
const sendBtn = $<HTMLButtonElement>("send");
const fileInput = $<HTMLInputElement>("file");

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const md = (s: string) =>
  esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a class="underline text-indigo-600" target="_blank" rel="noopener" href="$1">link</a>',
    )
    .replace(/\n/g, "<br>");

function add(role: "user" | "bot", html: string): HTMLDivElement {
  const d = document.createElement("div");
  d.className =
    role === "user"
      ? "ml-auto max-w-[80%] rounded-2xl bg-indigo-600 text-white px-4 py-2"
      : "mr-auto max-w-[85%] rounded-2xl bg-slate-100 px-4 py-2";
  d.innerHTML = html;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
  return d;
}

const list = (t: string, a: string | string[]) => {
  const items: string[] = Array.isArray(a) ? a : [a];
  return items.length
    ? `<b>${t}:</b><ul class="list-disc ml-5">${items.map((x: string) => `<li>${esc(x)}</li>`).join("")}</ul>`
    : "";
};
function resumeCard(r: Resume): string {
  return `<b>Parsed resume</b><br>
    <b>Name:</b> ${esc(r.name)}<br>
    <b>Contact:</b> ${esc(r.email)} ${esc(r.phone)}<br>
    <b>Designation:</b> ${esc(r.designation)}<br>
    <b>Experience:</b> ${r.experience_years} yrs<br>
    <b>Skills:</b> ${r.skills.map(esc).join(", ")}<br>
    ${list("Work", r.experience)}${list("Education", r.education)}${list("Projects", r.projects)}`;
}

async function ask(text: string, showUser = true) {
  if (showUser) add("user", esc(text));
  const wait = add("bot", "Thinking…");
  sendBtn.disabled = true;
  try {
    wait.innerHTML = md(await sendChat(text));
  } catch (e) {
    wait.innerHTML = esc((e as Error).message);
  }
  sendBtn.disabled = false;
  log.scrollTop = log.scrollHeight;
}

sendBtn.onclick = () => {
  const t = input.value.trim();
  if (!t) return;
  input.value = "";
  ask(t);
};
input.onkeydown = (e) => {
  if (e.key === "Enter") sendBtn.click();
};

$("attach").onclick = () => fileInput.click();
fileInput.onchange = async () => {
  const f = fileInput.files?.[0];
  if (!f) return;
  add("user", `📄 ${esc(f.name)}`);
  const wait = add("bot", "Reading your resume…");
  try {
    wait.innerHTML = resumeCard(await uploadResume(f));
    await ask("Recommend jobs that match my resume.", false);
  } catch (e) {
    wait.innerHTML = `⚠️ ${esc((e as Error).message)}`;
  }
  fileInput.value = "";
};

add(
  "bot",
  "Hi! Upload your resume with 📎 (PDF or DOCX) and I'll find matching jobs.",
);
