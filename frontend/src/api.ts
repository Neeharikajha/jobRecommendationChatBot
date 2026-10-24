import type { Resume } from "./types";

async function parse(res: Response){
    const data = await res.json().catch(()=>({}));
    if(!res.ok) throw new Error(data.error ?? `Request failed (${res.status})`)
    return data;
}
export async function uploadResume(file: File): Promise<Resume>{
    const fd = new FormData();
    fd.append("file", file);
    const data = await parse(await fetch("/api/upload/", {method: "POST", body: fd}))
    return data.resume;
}

export async function sendChat(message: string): Promise<string> {
    const data = await parse(await fetch("/api/chat/", {
        method: "POST",
        headers: {"Content-Type" : "application/json"},
        body: JSON.stringify({message}),
    }));
    return data.reply;
}