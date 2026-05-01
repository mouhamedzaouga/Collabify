import re

filepath = r'c:\Users\mouha_edbx2zz\OneDrive\Desktop\GLSI2\S2\PFA-Final\frontend\projectflow_app.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace static Data Store with dynamic fetch initialization
store_pattern = r"let members = \[\s*\{id:'u0'.*?let activity = \[\s*\{icon:'✅'.*?\];"
new_store = """let members = [];
let projects = [];
let tasks = [];
let messages = {};
let activity = [];

const STATUSES = ['todo','doing','review','done'];
const STATUS_LABELS = {todo:'📌 À faire',doing:'🔄 En cours',review:'👀 En revue',done:'✅ Terminé'};
const STATUS_COLORS = {todo:'var(--ink3)',doing:'var(--amber)',review:'var(--sky)',done:'var(--lime)'};
const PRI_LABELS = {high:'Haute',medium:'Moyen',low:'Faible'};

const API_BASE = "http://127.0.0.1:8000/api";

async function initData() {
  try {
    members = await fetch(API_BASE+'/members').then(r=>r.json());
    projects = await fetch(API_BASE+'/projects').then(r=>r.json());
    tasks = await fetch(API_BASE+'/tasks').then(r=>r.json());
    const dash = await fetch(API_BASE+'/projects/dashboard').then(r=>r.json()).catch(()=>({activity:[]}));
    activity = dash.activity || [];
    for(let p of projects) {
        messages[p.id] = await fetch(API_BASE+'/messages/'+p.id).then(r=>r.json()).catch(()=>[]);
    }
    renderHome();
    updateRailCounts();
    if(currentProject) renderProjDetail();
  } catch(e) {
    console.error(e);
  }
}"""
content = re.sub(store_pattern, new_store, content, flags=re.DOTALL)

# 2. CRUD Operations replacement
content = content.replace("function saveProject(){", "async function saveProject(){")
content = content.replace("projects.push(p);messages[p.id]=[];\n  addActivity('◫',`<strong>Vous</strong> avez créé le projet <strong>${name}</strong>`);\n  closeModal();renderProjects();updateRailCounts();toast('✅ Projet créé !');", 
"await fetch(API_BASE+'/projects/', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name, desc:document.getElementById('f-desc')?.value||'', color:document.getElementById('f-color')?.value||'#b8ff57', deadline:document.getElementById('f-deadline')?.value||'', status:document.getElementById('f-status')?.value||'active', members:mems})}); closeModal(); await initData(); nav('projects',null); toast('✅ Projet créé !');")

content = content.replace("function updateProject(pid){", "async function updateProject(pid){")
content = content.replace("p.status=document.getElementById('f-status')?.value||p.status;\n  closeModal();renderProjDetail();toast('✅ Projet mis à jour !');", 
"p.status=document.getElementById('f-status')?.value||p.status;\n  await fetch(API_BASE+'/projects/'+pid, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:p.name, desc:p.desc, color:p.color, deadline:p.deadline, status:p.status})}); closeModal(); await initData(); toast('✅ Projet mis à jour !');")

content = content.replace("function deleteCurrentProject(){", "async function deleteCurrentProject(){")
content = content.replace("currentProject=null;\n  nav('projects',null);toast('🗑️ Projet supprimé');", 
"await fetch(API_BASE+'/projects/'+currentProject, {method:'DELETE'}); currentProject=null;\n  await initData(); nav('projects',null);toast('🗑️ Projet supprimé');")

content = content.replace("function saveTask(){", "async function saveTask(){")
content = content.replace("tasks.push(t);\n  addActivity('📋',`<strong>Vous</strong> avez créé la tâche \"<strong>${title}</strong>\"`);\n  closeModal();\n  if(currentView==='proj-detail')renderPDContent();\n  if(currentView==='tasks')renderMyTasks();\n  updateRailCounts();toast('✅ Tâche créée !');", 
"const b = {pid: document.getElementById('f-pid')?.value||projects[0]?.id, title, desc: document.getElementById('f-desc')?.value||'', priority: document.getElementById('f-priority')?.value||'medium', status: document.getElementById('f-status')?.value||'todo', assignee: document.getElementById('f-assignee')?.value||'u0', tags: document.getElementById('f-tags')?.value.split(',').map(s=>s.trim()).filter(Boolean)||[]}; await fetch(API_BASE+'/tasks/', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}); closeModal(); await initData(); if(currentView==='tasks')nav('tasks',null); toast('✅ Tâche créée !');")

content = content.replace("function updateTask(tid){", "async function updateTask(tid){")
content = content.replace("t.tags=document.getElementById('f-tags')?.value.split(',').map(s=>s.trim()).filter(Boolean)||t.tags;\n  closeModal();\n  if(currentView==='proj-detail')renderPDContent();\n  if(currentView==='tasks')renderMyTasks();\n  updateRailCounts();toast('✅ Tâche mise à jour !');", 
"t.tags=document.getElementById('f-tags')?.value.split(',').map(s=>s.trim()).filter(Boolean)||t.tags;\n  await fetch(API_BASE+'/tasks/'+tid, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({title:t.title, desc:t.desc, priority:t.priority, status:t.status, assignee:t.assignee, tags:t.tags})}); closeModal(); await initData(); if(currentView==='tasks')nav('tasks',null); toast('✅ Tâche mise à jour !');")

content = content.replace("function deleteTask(tid){", "async function deleteTask(tid){")
content = content.replace("tasks=tasks.filter(x=>x.id!==tid);\n  if(currentView==='proj-detail')renderPDContent();\n  if(currentView==='tasks')renderMyTasks();\n  updateRailCounts();toast('🗑️ Tâche supprimée');", 
"await fetch(API_BASE+'/tasks/'+tid, {method:'DELETE'}); await initData(); if(currentView==='tasks')nav('tasks',null); toast('🗑️ Tâche supprimée');")

content = content.replace("function saveMember(){", "async function saveMember(){")
content = content.replace("members.push(m);\n  addActivity('👤',`<strong>${name}</strong> a rejoint l'équipe`);\n  closeModal();renderMembers();updateRailCounts();toast(`✅ ${name} ajouté(e) !`);", 
"await fetch(API_BASE+'/members/', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name, role, email:document.getElementById('f-email')?.value||'', color:colors[role]||'#5e5e88'})}); closeModal(); await initData(); nav('members',null); toast(`✅ ${name} ajouté(e) !`);")

content = content.replace("function updateMember(uid){", "async function updateMember(uid){")
content = content.replace("m.initials=m.name.split(' ').map(p=>p[0]).join('').slice(0,2).toUpperCase();\n  closeModal();renderMembers();toast('✅ Membre mis à jour !');", "m.initials=m.name.split(' ').map(p=>p[0]).join('').slice(0,2).toUpperCase();\n  await fetch(API_BASE+'/members/'+uid, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:m.name, email:m.email, role:m.role})}); closeModal(); await initData(); nav('members',null); toast('✅ Membre mis à jour !');")

content = content.replace("function deleteMember(uid){", "async function deleteMember(uid){")
content = content.replace("projects.forEach(p=>{p.members=p.members.filter(id=>id!==uid);});\n  renderMembers();toast('🗑️ Membre supprimé');", "await fetch(API_BASE+'/members/'+uid, {method:'DELETE'}); await initData(); nav('members',null);toast('🗑️ Membre supprimé');")

content = content.replace("function addMembersToProject(pid){", "async function addMembersToProject(pid){")
content = content.replace("checked.forEach(uid=>{if(!p.members.includes(uid))p.members.push(uid);});\n  closeModal();renderPDContent();toast(`✅ ${checked.length} membre(s) invité(s) !`);", "await fetch(API_BASE+'/projects/'+pid+'/members', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({member_ids:checked})}); closeModal(); await initData(); toast(`✅ ${checked.length} membre(s) invité(s) !`);")

content = content.replace("function removeMemberFromProject(uid){", "async function removeMemberFromProject(uid){")
content = content.replace("p.members=p.members.filter(id=>id!==uid);\n  renderPDContent();toast('✅ Membre retiré du projet');", "await fetch(API_BASE+'/projects/'+currentProject+'/members/'+uid, {method:'DELETE'}); await initData(); toast('✅ Membre retiré du projet');")

content = content.replace("function sendMsg(pid,type){", "async function sendMsg(pid,type){")
content = content.replace("messages[pid].push({id:'m'+Date.now(),uid:'u0',text:input.value.trim(),time:new Date().toLocaleTimeString('fr',{hour:'2-digit',minute:'2-digit'}),date:'Aujourd\\'hui'});\n  addActivity('💬',`<strong>Vous</strong> avez posté un message dans ${proj(pid)?.name||'un projet'}`);\n  input.value='';\n  if(type==='pd'){renderProjectChat(pid);}\n  else{renderChatRoom(pid);}", "await fetch(API_BASE+'/messages/'+pid, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({uid:'u0', text:input.value.trim()})}); input.value=''; await initData(); if(type==='pd'){renderProjectChat(pid);} else{renderChatRoom(pid);}")

# Intercept setTaskStatus 
content = content.replace("function setTaskStatus(tid,status){", "async function setTaskStatus(tid,status){")
content = content.replace("if(t){t.status=status;addActivity('🔄',`<strong>${ME.name.split(' ')[0]}</strong> a changé le statut de \"${t.title}\" → ${STATUS_LABELS[status]}`);}\n  renderPDContent();\n  if(currentView==='tasks')renderMyTasks();\n  if(currentView==='home')renderHome();\n  updateRailCounts();", "if(t){ await fetch(API_BASE+'/tasks/'+tid+'/status', {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status})}); await initData(); if(currentView==='tasks')renderMyTasks(); }")

# Change end INIT block
init_replace = "renderHome();updateRailCounts();\n</script>"
content = content.replace(init_replace, "initData();\n</script>")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied")
