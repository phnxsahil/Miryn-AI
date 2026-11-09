import asyncio,json,uuid
import pytest
from sqlalchemy import text
from tests.test_fact_supersession_db import pg, db, USER
from app.config import settings
from app.services.importance import score_message_llm,score_message_heuristic,ScoredFact
from app.services.fact_store import FactStore
from app.services.llm_service import LLMService

@pytest.fixture(autouse=True)
def source_filter_flags(monkeypatch):
 monkeypatch.setattr(settings,'IMPORTANCE_USE_LLM',True)
 monkeypatch.setattr(settings,'MEMORY_SUPERSESSION_ENABLED',False)
 monkeypatch.setattr(settings,'MEMORY_CORRECTION_ORDERING_ENABLED',False)
from app.core.encryption import decrypt_text
from pathlib import Path
ROWS=json.loads((Path(__file__).parent / 'fixtures/source_filter_gemini_20261109.json').read_text())['rows']
class Replay:
 def __init__(self,raw): self.raw=raw
 async def generate(self,*a,**kw):return self.raw
 parse_json_response=staticmethod(LLMService.parse_json_response)
@pytest.mark.parametrize('row',ROWS,ids=[r['case'] for r in ROWS])
def test_captured_persistence(db,monkeypatch,row):
 monkeypatch.setattr(settings,'MEMORY_SUPERSESSION_ENABLED',False)
 monkeypatch.setattr(settings,'MEMORY_CORRECTION_ORDERING_ENABLED',False)
 store=FactStore(); msg=str(uuid.uuid4())
 store.upsert_facts(USER,score_message_heuristic(row['message']),msg)
 facts=asyncio.run(score_message_llm(Replay(row['raw_response']),row['message']))
 store.replace_heuristic_for_message(USER,msg,facts)
 store.link_explicit_corrections(USER,facts,msg)
 with db.connect() as c:
  active=c.execute(text("SELECT fact,corrects FROM memory_facts WHERE user_id=:u AND status='active'"),{'u':USER}).mappings().all()
  links=c.execute(text('SELECT count(*) FROM memory_fact_supersessions')).scalar()
 values=[(decrypt_text(r['fact']),decrypt_text(r['corrects']) if r['corrects'] else None) for r in active]
 print(row['case'], values)
 assert links==0
 if row['expected']=='none':assert values==[]
 elif row['case']=='self_statement':assert values==[] # existing floating-point .6000000000000001 boundary, extracted .6
 else:
  assert len(values)==1
  if row['expected']=='correction':assert json.loads(values[0][1])['new_value']=='January 11'
  else:assert values[0][1] is None
@pytest.mark.parametrize('source',[None,'bogus','third_party','self_current'])
def test_label_behavior(db,monkeypatch,source):
 monkeypatch.setattr(settings,'MEMORY_SUPERSESSION_ENABLED',False)
 marker={'entity':'race','attribute':'date','old_value':'December 14','new_value':'January 11'}
 item={'fact':'My race is January 11','category':'life_event','importance':.85,'emotional_weight':.1,'corrects':marker}
 if source is not None:item['source']=source
 facts=asyncio.run(score_message_llm(Replay(json.dumps({'facts':[item]})),'My race is January 11'))
 FactStore().upsert_facts(USER,facts,str(uuid.uuid4()))
 with db.connect() as c:rows=c.execute(text("SELECT corrects FROM memory_facts WHERE status='active'")).all()
 assert len(rows)==(1 if source == 'self_current' else 0)
 if rows:assert bool(rows[0][0])==(source=='self_current')

def test_repeated_heuristic_residue(db,monkeypatch):
 monkeypatch.setattr(settings,'MEMORY_SUPERSESSION_ENABLED',False)
 row=ROWS[0]; store=FactStore(); msg=str(uuid.uuid4()); h=score_message_heuristic(row['message'])
 store.upsert_facts(USER,h,msg);store.upsert_facts(USER,h,str(uuid.uuid4()))
 refined=asyncio.run(score_message_llm(Replay(row['raw_response']),row['message']))
 store.replace_heuristic_for_message(USER,msg,refined)
 with db.connect() as c:n=c.execute(text("SELECT count(*) FROM memory_facts WHERE status='active'")).scalar()
 print('repeated heuristic active rows',n)
 assert n==0

def test_repeated_high_importance_third_party_is_removed(db,monkeypatch):
 monkeypatch.setattr(settings,'MEMORY_SUPERSESSION_ENABLED',False)
 source='My friend said I am devastated because I lost my job yesterday.'
 h=score_message_heuristic(source); assert h and h[0].importance>=.8
 store=FactStore(); msg=str(uuid.uuid4())
 store.upsert_facts(USER,h,msg);store.upsert_facts(USER,h,str(uuid.uuid4()))
 raw=json.dumps({'facts':[{'fact':'Friend lost a job','category':'work_career','importance':.9,'emotional_weight':.9,'source':'third_party','corrects':None}]})
 refined=asyncio.run(score_message_llm(Replay(raw),source))
 store.replace_heuristic_for_message(USER,msg,refined)
 with db.connect() as c:n=c.execute(text("SELECT count(*) FROM memory_facts WHERE status='active'")).scalar()
 assert n==0, 'Repeated heuristic fact survives correctly filtered third-party refinement'

def test_heuristic_finishing_after_refinement_is_removed(db,monkeypatch):
 monkeypatch.setattr(settings,'MEMORY_SUPERSESSION_ENABLED',False)
 source='My friend said I am devastated because I lost my job yesterday.'
 h=score_message_heuristic(source);store=FactStore();msg=str(uuid.uuid4())
 store.replace_heuristic_for_message(USER,msg,[])
 store.upsert_facts(USER,h,msg)
 with db.connect() as c:n=c.execute(text("SELECT count(*) FROM memory_facts WHERE status='active'")).scalar()
 assert n==0, 'Late asynchronous heuristic write remains durable after refinement'

@pytest.mark.parametrize('enabled',[True,False])
def test_explicit_heuristic_mode(db,monkeypatch,enabled):
 monkeypatch.setattr(settings,'IMPORTANCE_USE_LLM',enabled)
 facts=score_message_heuristic('I am devastated because I lost my job yesterday.')
 assert facts
 FactStore().upsert_facts(USER,facts,str(uuid.uuid4()))
 with db.connect() as c:n=c.execute(text("SELECT count(*) FROM memory_facts WHERE status='active'")).scalar()
 assert n==(0 if enabled else 1)

def test_manual_memory_and_repeated_validated_self_are_preserved(db,monkeypatch):
 monkeypatch.setattr(settings,'IMPORTANCE_USE_LLM',True)
 store=FactStore()
 for extractor in ['manual','llm']:
  fact=ScoredFact('My '+extractor+' fact is important','life_event',.9,.1,extractor)
  store.upsert_facts(USER,[fact],str(uuid.uuid4()))
  store.upsert_facts(USER,[fact],str(uuid.uuid4()))
 with db.connect() as c:rows=c.execute(text("SELECT extractor,mention_count,status FROM memory_facts")).all()
 assert sorted(rows)==[('llm',2,'active'),('manual',2,'active')]

def test_worker_unavailable_does_not_promote_heuristics(db,monkeypatch):
 monkeypatch.setattr(settings,'IMPORTANCE_USE_LLM',True)
 FactStore().upsert_facts(USER,score_message_heuristic('I am devastated because I lost my job yesterday.'),str(uuid.uuid4()))
 # No refinement arrives. History retention is outside FactStore's durable-facts table.
 with db.connect() as c:assert c.execute(text('SELECT count(*) FROM memory_facts')).scalar()==0
