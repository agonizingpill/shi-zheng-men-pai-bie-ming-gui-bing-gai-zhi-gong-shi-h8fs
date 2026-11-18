from sqlalchemy import text,inspect
from src.database import Session,Base,engine
from src.models import *
from src.security import password_hash
from src.common import rows

def ensure_columns():
 insp=inspect(engine)
 for table,col,ddl in [('registry','data_version','data_version INT NOT NULL DEFAULT 0'),('match_runs','data_version','data_version INT NOT NULL DEFAULT 0')]:
  if col not in [c['name'] for c in insp.get_columns(table)]:
   with engine.begin() as c:c.execute(text(f'ALTER TABLE {table} ADD COLUMN {ddl}'))

def seed():
 Base.metadata.create_all(engine)
 ensure_columns()
 with Session() as s:
  for role in ['operator','supervisor','viewer']:
   if not any(x.email==role+'@changqiao.local' for x in rows(s,User)):s.add(User(email=role+'@changqiao.local',password=password_hash('Address2026!'),role=role))
  if not s.get(Registry,1):s.add(Registry(id=1,now='2026-11-18T09:00:00',data_version=0))
  if not any(x.code=='CQ-018-A' for x in rows(s,Entrance)):
   for code,num,label,lat in [('CQ-018-A',18,'长桥路18号正门',31.210),('CQ-018-B',18,'长桥路十八号旧门牌',31.2101),('CQ-081',81,'长桥路81号',31.211),('CQ-018-C',18,'长桥路18号南入口',31.2102)]:
    e=Entrance(code=code,street='长桥路',number=num,label=label,lat=lat,lng=121.48);s.add(e);s.flush();a=Alias(entrance_id=e.id,text=label);s.add(a);s.flush();s.add(Evidence(alias_id=a.id,reference='照片-'+code,description='2026年11月现场门牌照片与老地籍图位置核验说明'))
   s.flush();es=rows(s,Entrance);p=Proposal(code='P031',source_id=es[1].id,target_id=es[0].id,reason='历史十八号门牌与现18号正门同宗同入口');s.add(p);s.flush();s.add(Objection(proposal_id=p.id,code='Y031',note='住户认为旧门牌对应独立南入口，申请现场复核',state='open'))
  s.flush();es=rows(s,Entrance)
  def ent(code):return next(x for x in es if x.code==code)
  def ensure_evidence(code,ref,desc):
   a=next(x for x in rows(s,Alias) if x.entrance_id==ent(code).id)
   if not any(x.reference==ref for x in rows(s,Evidence)):s.add(Evidence(alias_id=a.id,reference=ref,description=desc))
  ensure_evidence('CQ-018-A','地籍图-CQ-018-A','历史地籍图与门牌档案互证，正门位置与18号登记一致')
  ensure_evidence('CQ-018-B','地籍图-CQ-018-B','历史地籍图标注十八号与现18号同宗同位置')
  if not any(x.code=='P032' for x in rows(s,Proposal)):
   s.add(Proposal(code='P032',source_id=ent('CQ-018-C').id,target_id=ent('CQ-018-A').id,reason='南入口旧牌是否与正门同入口，住户说法待核'))
  s.commit()
if __name__=='__main__':seed()
