import{heading,form,select,area,badge}from'../components/registry.js';import{opts,esc}from'../utils/format.js';
export function render(d){return heading('04','首选不稳，先挂起。','同街同号候选先排首选；逐份撤去书证、排除失去佐证的别名后重排。首选消失、换了入口或并列即挂起，由核定员凭补录的独立书证放行；再补录别名或书证，旧放行作废。')+`<div class="split"><section>${d.proposals.map(x=>{let rel=d.releases.filter(r=>r.proposal_id===x.id).at(-1);let valid=rel&&rel.data_version===d.clock[0].data_version;return`<article><b>${esc(x.code)}</b> ${badge(x.state)}${valid?badge('released'):''}<p>入口 #${x.source_id} → #${x.target_id} · ${esc(x.reason)}</p><button data-verify="${x.id}">核验首选与书证</button></article>`}).join('')||'<p>尚无提案，先在归并候选页形成提案。</p>'}</section><aside id="verification-result"><h3>核验详情</h3><p>选择提案，查看原首选与逐份撤证后的重排结果。</p></aside></div>`}
export function detail(v,d){
 const code=id=>d.entrances.find(x=>x.id===id)?.code||'#'+id;
 const ref=id=>d.evidence.find(x=>x.id===id)?.reference||'#'+id;
 let b=v.baseline;
 let baseline=b.status==='ok'?`原首选 <b>${esc(code(b.preferred_id))}</b>${b.preferred_id===v.target_id?'（与提案目标一致）':'（与提案目标 '+esc(code(v.target_id))+' 不一致）'}`:b.status==='tie'?'原首选并列，无法唯一确定':'原首选消失（组内缺少有佐证的别名）';
 let scores=v.group.filter(id=>id!==v.source_id).map(id=>{let s=b.scores.find(x=>x.entrance_id===id);return`<tr><td>${esc(code(id))}</td><td>${s?s.score.toFixed(3):'无佐证别名'}</td></tr>`}).join('');
 let rows=v.sensitivity.map(x=>`<tr><td>${esc(x.reference)}</td><td>${badge(x.status)}</td><td>${x.status==='changed'?esc(code(x.preferred_id)):x.status==='tie'?'并列：'+x.tie_ids.map(id=>esc(code(id))).join('、'):x.status==='vanished'?'（首选消失）':'仍为 '+esc(code(b.preferred_id))}</td></tr>`).join('');
 let rel=v.release?(v.release.valid?`<p>有效放行：${esc(v.release.actor)} 凭书证 ${esc(ref(v.release.evidence_id))}（${esc(v.release.created)}）<br>${esc(v.release.note)}</p>`:`<p class="error">旧放行已作废：补录别名或书证后需重新放行。</p>`):'<p>尚无放行记录。</p>';
 let releaseForm='';
 if(v.verdict==='suspended'&&v.proposal_state==='draft'){
  let aids=d.aliases.filter(a=>v.group.includes(a.entrance_id)).map(a=>a.id);
  let evs=d.evidence.filter(e=>aids.includes(e.alias_id));
  releaseForm=form('release-'+v.proposal_id,'核定员凭独立书证放行','/proposals/'+v.proposal_id+'/release',select('evidence_id','独立书证',opts(evs,x=>x.reference))+area('note','放行依据','核定员现场复核，凭补录的独立书证确认首选入口，同意放行公示'));
 }
 return`<h3>核验详情 · 提案 #${v.proposal_id}</h3><p>${badge(v.verdict)} ${badge(v.match_fresh?'fresh':'stale')}</p><p>${baseline}</p><table><thead><tr><th>同街同号入口</th><th>与来源最大余弦</th></tr></thead><tbody>${scores}</tbody></table><h3>逐份撤去书证重排</h3><table><thead><tr><th>撤去书证</th><th>重排结果</th><th>首选变为</th></tr></thead><tbody>${rows}</tbody></table>${v.reasons.length?`<p class="error">${v.reasons.map(esc).join('<br>')}</p>`:'<p>逐份撤证后首选均不变，首选稳定。</p>'}${rel}${releaseForm}`}
