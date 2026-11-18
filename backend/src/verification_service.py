from sklearn.feature_extraction.text import TfidfVectorizer
from .models import Entrance,Alias,Evidence,MatchRun,Release,Registry,Proposal
from .common import *
from .matching import normalize
THRESHOLD=.2
def _scores(source_texts,others):
 all_texts=source_texts+[t for ts in others.values() for t in ts]
 if not source_texts or not others or len(all_texts)<2:return {}
 vec=TfidfVectorizer(analyzer='char',ngram_range=(1,3));v=vec.fit_transform([normalize(t) for t in all_texts])
 sv=v[:len(source_texts)];out={};i=len(source_texts)
 for eid,ts in others.items():out[eid]=round(float((sv@v[i:i+len(ts)].T).toarray().max()),6);i+=len(ts)
 return out
def _preferred(scores):
 qual={k:v for k,v in scores.items() if v>=THRESHOLD}
 if not qual:return None,'vanished',[]
 top=max(qual.values());best=sorted(k for k,v in qual.items() if abs(v-top)<1e-9)
 if len(best)>1:return None,'tie',best
 return best[0],'ok',best
def _group(s,p):
 src=get(s,Entrance,p.source_id)
 es=[x for x in rows(s,Entrance) if x.street==src.street and x.number==src.number]
 ids={x.id for x in es};als=[x for x in rows(s,Alias) if x.entrance_id in ids]
 aids={x.id for x in als};evs=[x for x in rows(s,Evidence) if x.alias_id in aids]
 return es,als,evs
def _rank(als,evs,source_id,removed=frozenset()):
 kept={}
 for e in evs:
  if e.id not in removed:kept[e.alias_id]=kept.get(e.alias_id,0)+1
 sup=[a for a in als if kept.get(a.id,0)>0]
 src=[a.text for a in sup if a.entrance_id==source_id];others={}
 for a in sup:
  if a.entrance_id!=source_id:others.setdefault(a.entrance_id,[]).append(a.text)
 return _scores(src,others)
def fresh(s,r):
 return any(x.state=='ready' and x.data_version>=r.data_version for x in rows(s,MatchRun))
def verify(s,p):
 es,als,evs=_group(s,p)
 base=_rank(als,evs,p.source_id);pref,bstatus,_=_preferred(base)
 sensitivity=[]
 for e in evs:
  pr,st,best=_preferred(_rank(als,evs,p.source_id,{e.id}))
  if st=='tie':out='tie'
  elif pr is None:out='vanished'
  elif pref is None or pr!=pref:out='changed'
  else:out='unchanged'
  sensitivity.append({'evidence_id':e.id,'reference':e.reference,'status':out,'preferred_id':pr,'tie_ids':best if st=='tie' else []})
 reasons=[]
 if bstatus=='vanished':reasons.append('原首选消失：同街同号组内缺少有书证佐证的别名')
 if bstatus=='tie':reasons.append('原首选并列，无法唯一确定目标入口')
 if bstatus=='ok' and pref!=p.target_id:reasons.append('原首选与提案目标入口不一致')
 for x in sensitivity:
  if x['status']=='changed':reasons.append(f"撤去书证{x['reference']}后首选变为入口#{x['preferred_id']}")
  if x['status']=='vanished':reasons.append(f"撤去书证{x['reference']}后首选消失")
  if x['status']=='tie':reasons.append(f"撤去书证{x['reference']}后首选并列")
 reg=s.get(Registry,1);rels=[x for x in rows(s,Release) if x.proposal_id==p.id];latest=rels[-1] if rels else None
 return {'proposal_id':p.id,'proposal_state':p.state,'source_id':p.source_id,'target_id':p.target_id,'data_version':reg.data_version,'group':[x.id for x in es],
 'baseline':{'status':bstatus,'preferred_id':pref,'scores':[{'entrance_id':k,'score':v} for k,v in sorted(base.items())]},
 'sensitivity':sensitivity,'verdict':'suspended' if reasons else 'clear','reasons':reasons,
 'release':({'id':latest.id,'evidence_id':latest.evidence_id,'actor':latest.actor,'note':latest.note,'created':latest.created,'valid':latest.data_version==reg.data_version} if latest else None),
 'match_fresh':fresh(s,reg)}
def release(s,id,d,u):
 r=lock(s);p=get(s,Proposal,id)
 if p.state!='draft':fail('只有草稿提案可以放行')
 v=verify(s,p)
 if v['verdict']=='clear':fail('提案首选稳定，无需放行')
 e=get(s,Evidence,d['evidence_id'])
 if e.alias_id not in {a.id for a in rows(s,Alias) if a.entrance_id in v['group']}:fail('书证不属于同街同号入口，不能作为独立放行依据')
 x=Release(proposal_id=p.id,evidence_id=e.id,note=d['note'],actor=u['email'],data_version=r.data_version,created=r.now);s.add(x);s.flush();return x
