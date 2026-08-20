const labels={active:"정상",watch:"확인 필요",inactive:"미활동"};
const state={data:null,github:"",selectedRepo:""};
const $=(q)=>document.querySelector(q);
const esc=(v)=>String(v??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
const githubParam=()=>new URLSearchParams(window.location.search).get("github")?.trim()??"";
const normalizeGithub=(value)=>value.trim().replace(/^@/,"").toLowerCase();

async function load(){
  try{
    const response=await fetch(`data/students.json?v=${Date.now()}`);
    if(!response.ok) throw new Error("data load failed");
    state.data=await response.json();
    state.github=normalizeGithub(githubParam());
    $("#courseTitle").textContent=state.data.course;
    $("#updatedAt").textContent=`마지막 동기화 · ${state.data.updatedAt}`;
    bind(); render();
  }catch(error){
    $("#dashboard").innerHTML='<div class="error">데이터를 불러오지 못했습니다. GitHub Pages 배포 상태와 data/students.json을 확인하세요.</div>';
  }
}

function bind(){
  window.addEventListener("popstate",()=>{
    state.github=normalizeGithub(githubParam());
    state.selectedRepo="";
    render();
  });
  $("#dashboard").addEventListener("submit",event=>{
    const form=event.target.closest("#githubLookupForm");
    if(!form) return;
    event.preventDefault();
    const input=form.querySelector('input[name="github"]');
    const github=normalizeGithub(input?.value??"");
    state.github=github;
    state.selectedRepo="";
    const nextUrl=github?`${window.location.pathname}?github=${encodeURIComponent(github)}`:window.location.pathname;
    window.history.pushState({github},"",nextUrl);
    render();
  });
  $("#dashboard").addEventListener("click",event=>{
    const repoButton=event.target.closest("[data-repo]");
    if(repoButton){
      state.selectedRepo=repoButton.dataset.repo;
      render();
      return;
    }
    if(event.target.closest("[data-reset-github]")){
      state.github="";
      state.selectedRepo="";
      window.history.pushState({github:""},"",window.location.pathname);
      render();
    }
  });
}

function matchedStudents(){
  const github=normalizeGithub(state.github);
  if(!github) return [];
  return state.data.students.filter(student=>normalizeGithub(student.github)===github);
}

function selectedStudent(students){
  if(!students.length) return null;
  const fallback=students[0].repo;
  if(!students.some(student=>student.repo===state.selectedRepo)) state.selectedRepo=fallback;
  return students.find(student=>student.repo===state.selectedRepo)??students[0];
}

function render(){
  const students=matchedStudents();
  if(!state.github){
    $("#dashboard").innerHTML=renderLookup();
    return;
  }
  if(!students.length){
    $("#dashboard").innerHTML=renderLookup(`GitHub ID "${esc(state.github)}"에 연결된 프로젝트를 찾지 못했습니다.`);
    return;
  }
  renderDashboard(students);
}

function renderLookup(message=""){
  return `
    <section class="lookup-card">
      <p class="lookup-eyebrow">개인별 프로젝트 조회</p>
      <h1>GitHub ID를 입력해 내 프로젝트만 확인하세요.</h1>
      <p class="lookup-copy">직접 접속 링크도 지원합니다. 예: <code>?github=shingugitvr000</code></p>
      <form id="githubLookupForm" class="lookup-form">
        <label class="lookup-input">
          <span>GitHub ID</span>
          <input name="github" placeholder="예: shingugitvr000" autocomplete="off" value="${esc(state.github)}">
        </label>
        <button type="submit">프로젝트 보기</button>
      </form>
      ${message?`<p class="lookup-message error">${message}</p>`:""}
    </section>`;
}

function renderDashboard(students){
  const s=selectedStudent(students); if(!s)return;
  const max=Math.max(...s.weekly,1); const total=s.weekly.reduce((a,b)=>a+b,0);
  const bars=s.weekly.map((value,index)=>`<div class="bar"><em>${value}</em><i style="height:${Math.max(8,value/max*100)}%"></i><small>${index+1}주</small></div>`).join("");
  const commits=s.recent.length?s.recent.map(c=>`<div class="commit"><span>⌘</span><div><strong>${esc(c.message)}</strong><p><code>${esc(c.sha)}</code> · ${esc(s.github)}</p></div><time>${esc(c.time)}</time></div>`).join(""):'<p class="empty">최근 커밋이 없습니다.</p>';
  const repoTabs=students.length>1?`<nav class="repo-switcher" aria-label="저장소 전환">${students.map(student=>`<button class="repo-tab ${student.repo===s.repo?"current":""}" data-repo="${esc(student.repo)}">${esc(student.repo)}</button>`).join("")}</nav>`:"";
  $("#dashboard").innerHTML=`
    <div class="dashboard-tools"><button class="ghost-button" type="button" data-reset-github>다른 GitHub ID 입력</button></div>
    <div class="student-head"><div><p>${esc(s.team)}</p><h1>${esc(s.name)}<small>${esc(s.id)}</small></h1><a href="https://github.com/${esc(s.github)}" target="_blank" rel="noopener">github.com/${esc(s.github)} ↗</a></div><span class="chip ${esc(s.status)}"><i></i>${esc(labels[s.status])}</span></div>
    ${repoTabs}
    <div class="metrics"><article><span>이번 주 커밋</span><strong>${s.commits}<small>회</small></strong><p>최근 7일 기준</p></article><article><span>활동한 날짜</span><strong>${s.activeDays}<small>/ 7일</small></strong><p>꾸준한 기록이 중요해요</p></article><article><span>마지막 커밋</span><strong class="time">${esc(s.lastCommit)}</strong><p>${esc(s.repo)}</p></article></div>
    <div class="content-grid"><article class="card"><div class="card-head"><div><h2>주차별 활동</h2><p>최근 7주 커밋 횟수</p></div><span>총 ${total}회</span></div><div class="chart">${bars}</div></article>
    <article class="card guide"><div class="card-head"><div><h2>이번 주 Notion 점검</h2><p>Git 기록만으로는 완료되지 않습니다</p></div></div><ol><li><span>01</span><div><strong>주간 목표</strong><p>구체적인 완료 기준까지 작성</p></div></li><li><span>02</span><div><strong>결과물 링크</strong><p>빌드·영상·이미지 연결</p></div></li><li><span>03</span><div><strong>문제 해결 기록</strong><p>시도와 해결 과정을 간단히 정리</p></div></li><li><span>04</span><div><strong>다음 주 계획</strong><p>우선순위와 담당 업무 확정</p></div></li></ol></article></div>
    <article class="card commits"><div class="card-head"><div><h2>최근 커밋</h2><p>${esc(s.repo)}</p></div><a href="https://github.com/${esc(s.repo)}/commits" target="_blank" rel="noopener">전체 보기 ↗</a></div><div>${commits}</div></article>`;
}
load();
