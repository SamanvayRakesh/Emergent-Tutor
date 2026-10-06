import ast, asyncio, importlib, sys, types, json
from pathlib import Path
import pytest
from fastapi import FastAPI, APIRouter, Request, HTTPException
from pydantic import BaseModel
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient

core=types.ModuleType('core');core.db=AsyncMongoMockClient().test;core.logger=types.SimpleNamespace(exception=lambda *a,**k:None,warning=lambda *a,**k:None)
sys.modules['core']=core
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'backend'))
import learning_evidence as le
from tutor_blocks import extract_cards
current_user={'user_id':'u','school':'nios','class_level':'10'}
async def user(_):return current_user
source=(ROOT / 'backend/routes/chat.py').read_text();tree=ast.parse(source)
names={'public_check','TutorCheckAnswer','answer_tutor_check','get_chat_session'}
module=ast.fix_missing_locations(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name in names],type_ignores=[]))
ns=dict(db=core.db,router=APIRouter(),BaseModel=BaseModel,Request=Request,HTTPException=HTTPException,get_current_user=user,learning_scope=le.learning_scope,chapter_mastery=le.chapter_mastery)
from datetime import datetime,timezone
ns.update(datetime=datetime,timezone=timezone)
exec(compile(module,'chat-routes','exec'),ns)
app=FastAPI();app.include_router(ns['router'],prefix='/api')

@pytest.fixture(autouse=True)
async def reset():
 global current_user
 current_user={'user_id':'u','school':'nios','class_level':'10'}
 for name in await core.db.list_collection_names():await core.db[name].delete_many({})

@pytest.mark.asyncio
async def test_unassessed_zero_and_scoping():
 assert (await le.chapter_mastery(current_user,'Transport','Business Studies'))['attempts']==0
 for school,grade,course in [('bnps','10',None),('nios','8',None),('nios','10','senior_secondary')]:
  await core.db.quizzes.insert_one({'user_id':'u','school':school,'class_level':grade,**({'course_id':course} if course else {}),'chapter':'Transport','subject':'Business Studies','completed':True,'correct_count':5,'total_questions':5})
 assert (await le.chapter_mastery(current_user,'Transport','Business Studies'))['attempts']==0

@pytest.mark.asyncio
async def test_quiz_and_check_shared_mastery():
 await core.db.quizzes.insert_one({**current_user,'chapter':'Transport','subject':'Business Studies','completed':True,'correct_count':3,'total_questions':5,'completed_at':'2026-10-05'})
 await core.db.tutor_checks.insert_one({**current_user,'chapter':'Transport','subject':'Business Studies','completed':True,'is_correct':True,'completed_at':'2026-10-06'})
 result=await le.chapter_mastery(current_user,'Transport','Business Studies')
 assert result['mastery_pct']==67 and result['attempts']==6
 records=await le.evidence_records(current_user);assert records[0]['mastery']==result['mastery_pct']

@pytest.mark.asyncio
async def test_weakness_improves_and_memory_is_scoped():
 await core.db.tutor_checks.insert_one({**current_user,'chapter':'Transport','subject':'Business Studies','completed':True,'is_correct':False,'completed_at':'1'})
 assert (await le.learning_memory(current_user,'Business Studies'))['weak_topics']==['Transport']
 for i in range(4):await core.db.tutor_checks.insert_one({**current_user,'chapter':'Transport','subject':'Business Studies','completed':True,'is_correct':True,'completed_at':str(i+2)})
 memory=await le.learning_memory(current_user,'Business Studies');assert memory['weak_topics']==[] and memory['strong_topics']==['Transport']
 assert (await le.learning_memory(current_user,'Mathematics'))['topics_tracked']==0

async def make_check():
 doc={**current_user,'check_id':'check1','session_id':'session1','subject':'Business Studies','chapter':'Transport','question':'Choose','options':['1','2','3','4'],'correct':'B','explanation':'Because','completed':False}
 await core.db.tutor_checks.insert_one(doc)
 return doc

@pytest.mark.asyncio
async def test_check_endpoint_persists_first_answer_and_reload():
 await make_check();await core.db.chat_sessions.insert_one({**current_user,'session_id':'session1'})
 await core.db.messages.insert_one({'session_id':'session1','role':'assistant','content':'Lesson','check_ids':['check1'],'timestamp':'1'})
 async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as c:
  first=await c.get('/api/chat/sessions/session1');card=first.json()['messages'][0]['checks'][0];assert 'correct' not in card and 'explanation' not in card
  response=await c.post('/api/chat/checks/check1/answer',json={'answer':'B'});assert response.status_code==200
  result=response.json();assert result['mastery']['attempts']==1 and result['check']['is_correct']
  again=await c.post('/api/chat/checks/check1/answer',json={'answer':'A'});assert again.json()['check']['selected']=='B' and again.json()['mastery']['attempts']==1
  reload=await c.get('/api/chat/sessions/session1');assert reload.json()['messages'][0]['checks'][0]['completed']

@pytest.mark.asyncio
async def test_check_concurrent_and_forbidden():
 await make_check()
 async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as c:
  replies=await asyncio.gather(*[c.post('/api/chat/checks/check1/answer',json={'answer':'B'}) for _ in range(4)])
  assert all(r.json()['mastery']['attempts']==1 for r in replies)
  assert (await c.post('/api/chat/checks/check1/answer',json={'answer':'Z'})).status_code==422
  current_user['school']='bnps'
  assert (await c.post('/api/chat/checks/check1/answer',json={'answer':'A'})).status_code==404

def test_cards_strip_answers_and_broken_json():
 check={'question':'Q','options':['a','b','c','d'],'correct':'A','explanation':'reason'}
 text,checks=extract_cards('Lesson [CHECK]'+json.dumps(check)+'[/CHECK]');assert text=='Lesson' and checks[0]['correct']=='A'
 assert 'secret' not in extract_cards('Lesson [CHECK]{"correct":"secret"')[0]

@pytest.mark.asyncio
async def test_full_generator_saves_cards_and_hides_answers():
 import uuid
 from tutor_blocks import extract_cards
 fn=next(n for n in ast.walk(tree) if isinstance(n,ast.AsyncFunctionDef) and n.name=='generate')
 fn.decorator_list=[];module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
 content='A square. [CHECK]'+json.dumps({'question':'2 squared?','options':['2','4','6','8'],'correct':'B','explanation':'2 times 2 is 4'})+'[/CHECK]' 
 class Stream:
  def __aiter__(self):self.used=False;return self
  async def __anext__(self):
   if self.used:raise StopAsyncIteration
   self.used=True;return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=content))])
  async def close(self):pass
 async def create(**kwargs):return Stream()
 charges=[]
 async def deduct(*args):charges.append(args);return {'deducted':2,'balance':98}
 async def noop(*args):pass
 env={**ns,'asyncio':asyncio,'json':json,'uuid':uuid,'logger':core.logger,'max_tokens':800,'ai_model':'test','ai_messages':[{'content':'test'}], 'session_id':'s','session':{'subject':'Mathematics','chapter':'Squares'},'user':current_user,'extract_cards':extract_cards,'openai_client':types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))), 'deduct_credits_for_chat':deduct,'increment_usage':noop,'record_token_usage':noop}
 exec(compile(module,'actual-generator','exec'),env)
 events=[json.loads(e[6:]) async for e in env['generate']()];done=events[-1]
 assert done['type']=='done' and done['content']=='A square.'
 assert len(done['checks'])==1 and 'correct' not in done['checks'][0] and len(charges)==1
 stored=await core.db.messages.find_one({'role':'assistant'});assert stored['check_ids']
 assert (await le.chapter_mastery(current_user,'Squares','Mathematics'))['attempts']==0

@pytest.mark.asyncio
async def test_progress_route_uses_shared_evidence_and_ignores_client_delta():
 progress_tree=ast.parse((ROOT / 'backend/routes/syllabus.py').read_text())
 selected=[n for n in progress_tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name in ('get_progress','update_progress')]
 module=ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[]))
 class ProgressUpdate(BaseModel):
  class_level:str;subject:str;chapter_id:str;chapter_name:str;mastery_delta:int=0
 env={**ns,'ProgressUpdate':ProgressUpdate,'evidence_records':le.evidence_records}
 exec(compile(module,'actual-progress','exec'),env)
 result=await env['update_progress'](ProgressUpdate(class_level='10',subject='Math',chapter_id='c',chapter_name='Squares',mastery_delta=100),None)
 assert result['mastery']==0
 await core.db.tutor_checks.insert_one({**current_user,'chapter':'Squares','subject':'Math','completed':True,'is_correct':True,'completed_at':'1'})
 progress=await env['get_progress'](None)
 assert progress['overall_mastery']==100 and progress['subject_progress']['Math']['avg_mastery']==100

@pytest.mark.asyncio
async def test_quiz_submit_retry_keeps_mastery_and_xp_once():
 quiz_tree=ast.parse((ROOT / 'backend/routes/quiz.py').read_text())
 fn=next(n for n in quiz_tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='submit_quiz');fn.decorator_list=[]
 class QuizSubmitRequest(BaseModel):answers:dict
 async def profile(_):return {}
 async def record(*args):pass
 env={**ns,'QuizSubmitRequest':QuizSubmitRequest,'get_student_profile':profile,'record_quiz_result':record,'measured_mastery':le.chapter_mastery,'has_school_curriculum':lambda *args:True,'get_school_chapters':lambda *args:[{'id':'c','name':'Squares'}]}
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'actual-quiz','exec'),env)
 await core.db.users.insert_one({**current_user,'xp':0,'level':1})
 await core.db.quizzes.insert_one({**current_user,'quiz_id':'q','subject':'Math','chapter':'Squares','topic':'Squares','completed':False,'created_at':'2020-01-01T00:00:00+00:00','questions':[{'question':'2 squared?','correct':'B'}]})
 result=await env['submit_quiz']('q',QuizSubmitRequest(answers={'0':'B'}),None)
 xp=(await core.db.users.find_one({'user_id':'u'}))['xp'];assert xp>0 and result['score']==100
 again=await env['submit_quiz']('q',QuizSubmitRequest(answers={'0':'A'}),None)
 assert again==result and (await core.db.users.find_one({'user_id':'u'}))['xp']==xp
 assert (await le.chapter_mastery(current_user,'Squares','Math'))['attempts']==1
 current_user['school']='bnps'
 with pytest.raises(HTTPException) as exc:await env['submit_quiz']('q',QuizSubmitRequest(answers={'0':'A'}),None)
 assert exc.value.status_code==404

@pytest.mark.asyncio
@pytest.mark.parametrize('attempts,expected', [([[],['ok']], ['reset','chunk','done']), ([['partial',RuntimeError('lost')],['ok']], ['chunk','reset','chunk','done']), ([[],[]], ['reset','error'])])
async def test_actual_tutor_retries_preserve_final_reply(attempts,expected):
 import uuid
 from tutor_blocks import extract_cards
 fn=next(n for n in ast.walk(tree) if isinstance(n,ast.AsyncFunctionDef) and n.name=='generate');fn.decorator_list=[]
 class Stream:
  def __init__(self,items):self.items=iter(items)
  def __aiter__(self):return self
  async def __anext__(self):
   try:x=next(self.items)
   except StopIteration:raise StopAsyncIteration
   if isinstance(x,Exception):raise x
   return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=x))])
  async def close(self):pass
 responses=iter(attempts)
 async def create(**kwargs):return Stream(next(responses))
 charges=[]
 async def deduct(*args):charges.append(args);return {'deducted':2,'balance':98}
 async def noop(*args):pass
 env={**ns,'asyncio':asyncio,'json':json,'uuid':uuid,'logger':core.logger,'max_tokens':800,'ai_model':'test','ai_messages':[{'content':'test'}], 'session_id':'s','session':{'subject':'Mathematics','chapter':'Squares'},'user':current_user,'extract_cards':extract_cards,'openai_client':types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))), 'deduct_credits_for_chat':deduct,'increment_usage':noop,'record_token_usage':noop}
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'actual-generator','exec'),env)
 events=[json.loads(e[6:]) async for e in env['generate']()]
 assert [e['type'] for e in events]==expected
 assert len(charges)==int(expected[-1]=='done')
 if expected[-1]=='done':assert events[-1]['content']=='ok'
