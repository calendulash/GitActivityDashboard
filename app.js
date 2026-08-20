const labels={active:"정상",watch:"확인 필요",inactive:"미활동"};
const state={data:null,selectedId:null,filter:"all",query:""};
const $=(q)=>document.querySelector(q);
const esc=(v)=>String(v??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));

async function load(){
  try{
    const response=await fetch(`data/students.json?v=${Date.now()}`);
    if(!response.ok) throw new Error("data load failed");
    state.data=await response.json();
    state.selectedId=state.data.students[0]?.id??null;
    $("#courseTitle").textContent=state.data.course;
    $("#updatedAt").textContent=`마지막 동기화 · ${state.data.updatedAt}`;
    $("#notionLink").href=state.data.notionUrl||"https://www.notion.so";
    bind(); render();
  }catch(error){
    $("#dashboard").innerHTML='<div class="error">데이터를 불러오지 못했습니다. GitHub Pages 배포 상태와 data/students.json을 확인하세요.</div>';
  }
}

function bind(){
  $("#searchInput").addEventListener("input",e=>{state.query=e.target.value.toLowerCase();renderList()});
  document.querySelectorAll("[data-filter]").forEach(button=>button.addEventListener("click",()=>{
    state.filter=button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach(x=>x.classList.toggle("active",x===button));
    renderList();
  }));
}

function visibleStudents(){return state.data.students.filter(s=>{
  const text=`${s.name} ${s.id} ${s.team}`.toLowerCase();
  return text.includes(state.query)&&(state.filter==="all"||s.status===state.filter);
})}

function render(){renderList();renderDashboard()}
function renderList(){
  const students=visibleStudents(); $("#studentCount").textContent=`${state.data.students.length}명`;
  $("#studentList").innerHTML=students.length?students.map(s=>`<button class="student ${s.id===state.selectedId?"current":""}" data-id="${esc(s.id)}"><span class="avatar">${esc(s.name.slice(-2))}</span><span class="identity"><strong>${esc(s.name)}</strong><small>${esc(s.id)} · ${esc(s.team)}</small></span><i class="dot ${esc(s.status)}" title="${esc(labels[s.status])}"></i></button>`).join(""):'<p class="empty">검색 결과가 없습니다.</p>';
  document.querySelectorAll(".student").forEach(button=>button.addEventListener("click",()=>{state.selectedId=button.dataset.id;render()}));
}

function renderDashboard(){
  const s=state.data.students.find(x=>x.id===state.selectedId); if(!s)return;
  const max=Math.max(...s.weekly,1); const total=s.weekly.reduce((a,b)=>a+b,0);
  const bars=s.weekly.map((value,index)=>`<div class="bar"><em>${value}</em><i style="height:${Math.max(8,value/max*100)}%"></i><small>${index+1}주</small></div>`).join("");
  const commits=s.recent.length?s.recent.map(c=>`<div class="commit"><span>⌘</span><div><strong>${esc(c.message)}</strong><p><code>${esc(c.sha)}</code> · ${esc(s.github)}</p></div><time>${esc(c.time)}</time></div>`).join(""):'<p class="empty">최근 커밋이 없습니다.</p>';
  $("#dashboard").innerHTML=`
    <div class="student-head"><div><p>${esc(s.team)}</p><h1>${esc(s.name)}<small>${esc(s.id)}</small></h1><a href="https://github.com/${esc(s.github)}" target="_blank" rel="noopener">github.com/${esc(s.github)} ↗</a></div><span class="chip ${esc(s.status)}"><i></i>${esc(labels[s.status])}</span></div>
    <div class="metrics"><article><span>이번 주 커밋</span><strong>${s.commits}<small>회</small></strong><p>최근 7일 기준</p></article><article><span>활동한 날짜</span><strong>${s.activeDays}<small>/ 7일</small></strong><p>꾸준한 기록이 중요해요</p></article><article><span>마지막 커밋</span><strong class="time">${esc(s.lastCommit)}</strong><p>${esc(s.repo)}</p></article></div>
    <div class="content-grid"><article class="card"><div class="card-head"><div><h2>주차별 활동</h2><p>최근 7주 커밋 횟수</p></div><span>총 ${total}회</span></div><div class="chart">${bars}</div></article>
    <article class="card guide"><div class="card-head"><div><h2>이번 주 Notion 점검</h2><p>Git 기록만으로는 완료되지 않습니다</p></div></div><ol><li><span>01</span><div><strong>주간 목표</strong><p>구체적인 완료 기준까지 작성</p></div></li><li><span>02</span><div><strong>결과물 링크</strong><p>빌드·영상·이미지 연결</p></div></li><li><span>03</span><div><strong>문제 해결 기록</strong><p>시도와 해결 과정을 간단히 정리</p></div></li><li><span>04</span><div><strong>다음 주 계획</strong><p>우선순위와 담당 업무 확정</p></div></li></ol></article></div>
    <article class="card commits"><div class="card-head"><div><h2>최근 커밋</h2><p>${esc(s.repo)}</p></div><a href="https://github.com/${esc(s.repo)}/commits" target="_blank" rel="noopener">전체 보기 ↗</a></div><div>${commits}</div></article>`;
}
load();
