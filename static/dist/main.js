"use strict";(()=>{var m=document.getElementById("log"),f=document.getElementById("msg-input"),x=document.getElementById("send-btn"),p=document.getElementById("file-input"),E=document.getElementById("attach-btn"),y=document.getElementById("resume-badge");async function h(e){let s=await e.json().catch(()=>({}));if(!e.ok)throw new Error(s.error??`Error ${e.status}`);return s}async function L(e){let s=new FormData;return s.append("file",e),(await h(await fetch("/api/upload/",{method:"POST",body:s}))).resume}async function T(e){return await h(await fetch("/api/chat/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:e})}))}function a(e){return String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function g(){m.scrollTop=m.scrollHeight}function o(e,s){let n=document.createElement("div");if(e==="user"){n.className="flex justify-end";let t=document.createElement("div");t.className="max-w-xl bg-neutral-100 text-neutral-950 font-normal text-sm px-4 py-2.5 rounded-lg border border-neutral-300 shadow-sm",typeof s=="string"?t.innerHTML=s:t.appendChild(s),n.appendChild(t)}else{n.className="flex justify-start w-full";let t=document.createElement("div");t.className="max-w-2xl w-full bg-neutral-950 text-neutral-200 text-sm p-4 rounded-lg border border-neutral-800 leading-relaxed",typeof s=="string"?t.innerHTML=s:(t.className="w-full",t.appendChild(s)),n.appendChild(t)}return m.appendChild(n),g(),n}function w(){let e=document.createElement("div");return e.className="flex justify-start w-full",e.innerHTML=`
    <div class="bg-neutral-950 border border-neutral-800 rounded-lg px-4 py-3 flex items-center gap-1.5">
      <span class="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-pulse"></span>
      <span class="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-pulse delay-100"></span>
      <span class="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-pulse delay-200"></span>
      <span class="text-xs text-neutral-400 font-mono ml-2 uppercase tracking-widest">Thinking</span>
    </div>
  `,m.appendChild(e),g(),e}function H(e){return a(e).replace(/\*\*(.+?)\*\*/g,"<strong class='text-white font-semibold'>$1</strong>").replace(/\n/g,"<br>")}function M(e){let s=(e.name||"?").split(" ").map(l=>l[0]).slice(0,2).join("").toUpperCase(),n=(e.skills||[]).map(l=>`<span class="text-xs px-2 py-0.5 rounded border border-neutral-700 bg-neutral-900 text-neutral-300 font-mono">${a(l)}</span>`).join(""),t=Array.isArray(e.experience)?e.experience.map(l=>`<li class="text-neutral-400 text-xs">${a(l)}</li>`).join(""):"",r=(e.education||[]).map(l=>`<li class="text-neutral-400 text-xs">${a(l)}</li>`).join(""),c=(e.projects||[]).map(l=>`<li class="text-neutral-400 text-xs">${a(l)}</li>`).join(""),d=document.createElement("div");return d.className="border border-neutral-800 bg-neutral-950 rounded-lg p-5 space-y-4 w-full",d.innerHTML=`
    <div class="flex items-center gap-3 pb-3 border-b border-neutral-800">
      <div class="w-10 h-10 rounded bg-white text-black font-bold flex items-center justify-center text-sm uppercase">
        ${s}
      </div>
      <div>
        <div class="text-base font-semibold text-white tracking-tight">${a(e.name||"Candidate Resume")}</div>
        <div class="text-xs text-neutral-400">${a(e.designation||"Applicant")}</div>
      </div>
    </div>

    <div class="space-y-3 text-xs">
      ${e.email||e.phone?`
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Contact</span>
        <span class="text-neutral-300">${a(e.email||"")}${e.email&&e.phone?" \xB7 ":""}${a(e.phone||"")}</span>
      </div>`:""}
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Experience</span>
        <span class="text-neutral-300">${e.experience_years} year(s)</span>
      </div>
      ${n?`
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Skills</span>
        <div class="flex flex-wrap gap-1.5 flex-1">${n}</div>
      </div>`:""}
      ${t?`
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Work</span>
        <ul class="list-disc list-inside space-y-1 flex-1">${t}</ul>
      </div>`:""}
      ${r?`
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Education</span>
        <ul class="list-disc list-inside space-y-1 flex-1">${r}</ul>
      </div>`:""}
      ${c?`
      <div class="flex flex-col sm:flex-row sm:gap-4">
        <span class="w-24 text-neutral-500 font-medium uppercase tracking-wider text-[11px]">Projects</span>
        <ul class="list-disc list-inside space-y-1 flex-1">${c}</ul>
      </div>`:""}
    </div>

    <div class="pt-3 border-t border-neutral-800 text-[11px] text-neutral-400 font-mono uppercase tracking-wider">
      Resume parsed successfully. Ask me to find matching jobs or suggest roles.
    </div>
  `,d}function j(e){let s=document.createElement("div");s.className="border border-neutral-800 bg-neutral-950 rounded-lg overflow-hidden transition-all duration-150 hover:border-neutral-600";let n=e.remote?'<span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded border border-neutral-700 bg-neutral-900 text-neutral-300">Remote</span>':"",t=e.experience_required?`<span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded border border-neutral-800 bg-black text-neutral-400">${a(String(e.experience_required))}</span>`:"",r=(e.skills||[]).slice(0,8).map(i=>`<span class="text-xs px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-neutral-300 font-mono">${a(i)}</span>`).join(""),c=e.description_snippet?`<div class="space-y-1">
        <div class="text-[11px] uppercase tracking-wider text-neutral-500 font-medium">Description</div>
        <div class="text-xs text-neutral-300 leading-relaxed">${a(e.description_snippet)}\u2026</div>
       </div>`:"";s.innerHTML=`
    <div class="jc-summary p-4 flex items-start justify-between cursor-pointer select-none bg-neutral-950 hover:bg-neutral-900/50 transition-colors">
      <div class="space-y-1">
        <div class="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">Job ${e.display_id}</div>
        <div class="text-sm font-semibold text-white tracking-tight">${a(e.title)}</div>
        <div class="text-xs text-neutral-400 font-normal">${a(e.company)} \xB7 ${a(e.location)}</div>
        <div class="flex items-center gap-1.5 pt-1">
          ${n}
          ${t}
        </div>
      </div>
      <div class="jc-chevron text-neutral-400 text-sm font-mono transition-transform duration-200">
        &#8595;
      </div>
    </div>
    <div class="jc-body hidden border-t border-neutral-800 p-4 space-y-4 bg-black">
      ${c}
      ${r?`<div class="space-y-1.5">
        <div class="text-[11px] uppercase tracking-wider text-neutral-500 font-medium">Required Skills</div>
        <div class="flex flex-wrap gap-1">${r}</div>
      </div>`:""}
      <div class="flex items-center gap-2 pt-2 border-t border-neutral-900">
        ${e.source_link?`<button class="jc-link-btn px-3 py-1.5 bg-white text-black hover:bg-neutral-200 text-xs font-semibold rounded uppercase tracking-wider transition-colors cursor-pointer" data-link="${a(e.source_link)}">Apply on site</button>`:""}
        <button class="jc-apply-btn px-3 py-1.5 border border-neutral-700 bg-neutral-900 hover:bg-neutral-800 text-neutral-200 text-xs font-semibold rounded uppercase tracking-wider transition-colors cursor-pointer" data-apply="${e.display_id}">Mark as applied</button>
      </div>
    </div>
  `;let d=s.querySelector(".jc-summary"),l=s.querySelector(".jc-body"),v=s.querySelector(".jc-chevron");return d.addEventListener("click",()=>{l.classList.contains("hidden")?(l.classList.remove("hidden"),v.innerHTML="&#8593;"):(l.classList.add("hidden"),v.innerHTML="&#8595;"),g()}),s.querySelectorAll("[data-link]").forEach(i=>{i.addEventListener("click",b=>{b.stopPropagation(),window.open(i.dataset.link,"_blank","noopener")})}),s.querySelectorAll("[data-apply]").forEach(i=>{i.addEventListener("click",b=>{b.stopPropagation();let $=i.dataset.apply;k(`apply to ${$}`,!0),i.textContent="Applied",i.disabled=!0,i.classList.add("opacity-50","cursor-not-allowed")})}),s}function D(e,s){let n=document.createElement("div");return n.className="space-y-3 w-full",n.innerHTML=`<div class="text-xs font-mono uppercase tracking-wider text-neutral-400 border-b border-neutral-800 pb-2">${a(s)}</div>`,e.forEach(t=>n.appendChild(j(t))),n}function _(e,s){let n=e.map(r=>`
    <tr class="border-b border-neutral-800/60 hover:bg-neutral-900/40 text-xs">
      <td class="p-3 text-neutral-500 font-mono">${r.index}</td>
      <td class="p-3"><strong class="text-white">${a(r.title)}</strong><br><span class="text-neutral-400 text-[11px]">${a(r.company)}</span></td>
      <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-mono border border-neutral-700 bg-neutral-900 text-neutral-300 uppercase">${a(r.status)}</span></td>
      <td class="p-3 text-neutral-400 font-mono text-[11px]">${a(r.date)}</td>
    </tr>`).join(""),t=document.createElement("div");return t.className="w-full space-y-3 border border-neutral-800 rounded-lg p-4 bg-neutral-950",t.innerHTML=`
    <div class="text-xs font-mono uppercase tracking-wider text-neutral-400 border-b border-neutral-800 pb-2">${a(s)}</div>
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
        <tbody>${n}</tbody>
      </table>
    </div>
  `,t}var u=!1;async function k(e,s=!0){if(u)return;u=!0,x.disabled=!0,s&&o("user",a(e));let n=w();try{let t=await T(e);if(n.remove(),t.reply&&o("bot",H(t.reply)),t.type==="jobs"&&t.jobs&&t.jobs.length>0){let r=D(t.jobs,`${t.jobs.length} matching jobs`);o("bot",r)}else if(t.type==="applications"&&t.applications){let r=_(t.applications,`${t.applications.length} application(s)`);o("bot",r)}}catch(t){n.remove(),o("bot",`<span class="text-neutral-400 font-mono">${a(t.message)}</span>`)}finally{u=!1,x.disabled=!1,g()}}x.addEventListener("click",()=>{let e=f.value.trim();!e||u||(f.value="",k(e))});f.addEventListener("keydown",e=>{e.key==="Enter"&&!e.shiftKey&&x.click()});E.addEventListener("click",()=>p.click());p.addEventListener("change",async()=>{let e=p.files?.[0];if(!e)return;p.value="",o("user",`Uploaded resume: ${a(e.name)}`);let s=w();try{let n=await L(e);s.remove();let t=M(n);o("bot",t),y.classList.remove("hidden"),y.classList.add("inline-block")}catch(n){s.remove(),o("bot",`<span class="text-neutral-400 font-mono">Could not parse resume: ${a(n.message)}</span>`)}});o("bot","Welcome to Hidani Job Assistant.<br><br>Upload your resume using the paperclip icon or ask commands below:<br><strong class='text-white'>Find jobs</strong> \u2014 'Show me frontend developer jobs'<br><strong class='text-white'>Filter</strong> \u2014 'Only remote roles' or 'Jobs needing Python'<br><strong class='text-white'>Suggest roles</strong> \u2014 'What roles can I apply to?'<br><strong class='text-white'>Apply</strong> \u2014 'Apply to jobs 1, 2, 3'<br><strong class='text-white'>Track</strong> \u2014 'Show my applied jobs'");})();
