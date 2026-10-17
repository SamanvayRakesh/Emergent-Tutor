"""Credential-free lifecycle tests for the actual visual-job handlers."""
import ast
import asyncio
import copy
import hashlib
import json
import logging
import re
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail

class Collection:
    def __init__(self): self.rows = []
    def matches(self, row, query):
        return all(row.get(k) in v['$in'] if isinstance(v, dict) and '$in' in v else row.get(k) == v for k, v in query.items())
    async def find_one(self, query, *projection):
        return next((copy.deepcopy(row) for row in self.rows if self.matches(row, query)), None)
    async def insert_one(self, row): self.rows.append(copy.deepcopy(row))
    async def update_one(self, query, update, upsert=False):
        row = next((row for row in self.rows if self.matches(row, query)), None)
        inserted = row is None
        if inserted:
            if not upsert: return NS(modified_count=0)
            row = dict(query); self.rows.append(row)
            row.update(copy.deepcopy(update.get('$setOnInsert', {})))
        before = copy.deepcopy(row)
        row.update(copy.deepcopy(update.get('$set', {})))
        return NS(modified_count=int(inserted or row != before))

CONTENT = 'Visualize: Revision Notes for Fractions\n\n[STUDYVISUAL INSTRUCTIONS]\nGenerate'

def environment():
    db = NS(visual_jobs=Collection(), messages=Collection(), chat_sessions=Collection())
    db.chat_sessions.rows.append({'session_id':'s','user_id':'u','class_level':'10'})
    router = NS(post=lambda *a, **kw: lambda f:f, get=lambda *a, **kw: lambda f:f)
    ns = dict(asyncio=asyncio, hashlib=hashlib, json=json, re=re, datetime=datetime,
              timezone=timezone, HTTPException=HTTPException, Request=object,
              VisualJobRequest=object, db=db, logger=logging.getLogger('visual-jobs'),
              get_current_user=AsyncMock(return_value={'user_id':'u','class_level':'10'}),
              ensure_credits=AsyncMock(), router=router, _TASKS={}, _TERMINAL={'completed','failed','cancelled'})
    tree = ast.parse((Path(__file__).resolve().parents[1]/'visual_jobs.py').read_text())
    nodes = [node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'visual_jobs','exec'),ns)
    return ns, db

class Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.ns,self.db=environment(); self.request=NS(state=NS()); self.body=NS(content=CONTENT,request_id='request_123456789')
    async def asyncTearDown(self):
        tasks=list(self.ns['_TASKS'].values())
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
    async def seed(self):
        self.ns['_schedule']=lambda *args:None
        return await self.ns['create_visual_job']('s',self.body,self.request)
    async def response(self, events):
        async def stream():
            for event in events: yield 'data: '+json.dumps(event)+'\n\n'
        return NS(body_iterator=stream())
    async def test_lost_create_response_and_duplicate_workers_generate_once(self):
        job=await self.seed(); again=await self.ns['create_visual_job']('s',self.body,self.request)
        self.assertEqual(job['job_id'],again['job_id']); self.assertEqual(len(self.db.visual_jobs.rows),1)
        generated=AsyncMock(return_value=await self.response([
            {'type':'accepted','total_topics':2},{'type':'visual_partial','content':'first'},
            {'type':'visual_ready','content':'complete'},{'type':'done','message_id':'m','credits_used':2}]))
        self.ns['_visual_response']=generated
        await asyncio.gather(self.ns['_run'](job['job_id'],self.request),self.ns['_run'](job['job_id'],self.request))
        generated.assert_awaited_once(); self.assertEqual(len(self.db.messages.rows),1)
        result=await self.ns['get_visual_job'](job['job_id'],self.request)
        self.assertEqual(result['status'],'completed'); self.assertEqual(result['content'],'complete'); self.assertEqual(result['receipt']['credits_used'],2)
        replay=await self.ns['create_visual_job']('s',self.body,self.request)
        self.assertEqual(replay['status'],'completed'); generated.assert_awaited_once()
    async def test_failed_generation_keeps_partial_topics(self):
        job=await self.seed()
        self.ns['_visual_response']=AsyncMock(return_value=await self.response([
            {'type':'visual_partial','content':'finished topics'}, {'type':'error','code':'GENERATION_FAILED','message':'Try again'}]))
        await self.ns['_run'](job['job_id'],self.request)
        result=await self.ns['get_visual_job'](job['job_id'],self.request)
        self.assertEqual(result['status'],'failed'); self.assertEqual(result['content'],'finished topics');self.assertFalse(result['ready'])
    async def test_unexpected_end_cannot_report_completion(self):
        job=await self.seed();self.ns['_visual_response']=AsyncMock(return_value=await self.response([{'type':'visual_ready','content':'unconfirmed'}]))
        await self.ns['_run'](job['job_id'],self.request)
        result=await self.ns['get_visual_job'](job['job_id'],self.request)
        self.assertEqual(result['status'],'failed'); self.assertEqual(result['content'],'unconfirmed')
    async def test_saved_result_recovered_without_regeneration(self):
        job=await self.seed();self.db.messages.rows.append({'visual_job_id':job['job_id'],'role':'assistant','session_id':'s','message_id':'m','content':'saved','receipt':{'credits_used':1}})
        self.ns['_visual_response']=AsyncMock(side_effect=AssertionError('Must not regenerate'))
        await self.ns['_run'](job['job_id'],self.request)
        result=await self.ns['get_visual_job'](job['job_id'],self.request)
        self.assertEqual(result['status'],'completed');self.assertEqual(result['content'],'saved');self.ns['_visual_response'].assert_not_awaited()
    async def test_cancel_before_lost_create_prevents_generation(self):
        self.ns['_schedule']=lambda *args:None
        cancelled=await self.ns['cancel_visual_request']('s',self.body,self.request)
        created=await self.ns['create_visual_job']('s',self.body,self.request)
        self.assertEqual(cancelled['status'],'cancelled');self.assertEqual(created['status'],'cancelled');self.ns['ensure_credits'].assert_not_awaited()
    async def test_cancel_running_closes_generator(self):
        job=await self.seed();started=asyncio.Event();closed=asyncio.Event()
        async def stream():
            try:
                yield 'data: '+json.dumps({'type':'visual_partial','content':'first'})+'\n\n'
                started.set(); await asyncio.Event().wait()
            finally: closed.set()
        self.ns['_visual_response']=AsyncMock(return_value=NS(body_iterator=stream()))
        task=asyncio.create_task(self.ns['_run'](job['job_id'],self.request));self.ns['_TASKS'][job['job_id']]=task
        await started.wait();result=await self.ns['cancel_visual_job'](job['job_id'],self.request)
        await asyncio.gather(task,return_exceptions=True)
        self.assertEqual(result['status'],'cancelled');self.assertTrue(closed.is_set());self.assertEqual(result['content'],'first')
    async def test_cancel_does_not_discard_saved_answer(self):
        job=await self.seed();self.db.messages.rows.append({'visual_job_id':job['job_id'],'role':'assistant','session_id':'s','message_id':'m','content':'saved'})
        result=await self.ns['cancel_visual_job'](job['job_id'],self.request)
        self.assertEqual(result['status'],'completed');self.assertFalse(result['receipt']['receipt_confirmed'])
    async def test_stale_worker_fails_instead_of_hanging(self):
        job=await self.seed();self.db.visual_jobs.rows[0].update(status='running',updated_at=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat())
        result=await self.ns['get_visual_job'](job['job_id'],self.request)
        self.assertEqual(result['error']['code'],'WORKER_INTERRUPTED');self.assertEqual(result['status'],'failed')
    async def test_ownership_grade_and_request_id_guards(self):
        job=await self.seed();self.ns['get_current_user'].return_value={'user_id':'other','class_level':'10'}
        with self.assertRaises(HTTPException) as caught:await self.ns['get_visual_job'](job['job_id'],self.request)
        self.assertEqual(caught.exception.status_code,404)
        self.ns['get_current_user'].return_value={'user_id':'u','class_level':'11'}
        with self.assertRaises(HTTPException) as caught:await self.ns['create_visual_job']('s',self.body,self.request)
        self.assertEqual(caught.exception.status_code,403)
        self.ns['get_current_user'].return_value={'user_id':'u','class_level':'10'}
        with self.assertRaises(HTTPException):await self.ns['create_visual_job']('s',NS(content='ordinary prose',request_id='request_123456789'),self.request)
        with self.assertRaises(HTTPException) as caught:await self.ns['create_visual_job']('s',NS(content=CONTENT+' changed',request_id=self.body.request_id),self.request)
        self.assertEqual(caught.exception.status_code,409)
    async def test_real_generator_saves_and_charges_once_without_waiting_for_analytics(self):
        from test_diagram_generation import namespace, Stream, MAP
        job=await self.seed()
        self.ns['get_current_user'].return_value['school']='nios'
        self.db.chat_sessions.rows[0].update(subject='Mathematics',chapter='Fractions')
        self.db.users=Collection();self.db.users.rows.append({'user_id':'u','xp':10,'level':1})
        class Cursor:
            def sort(self,*a):return self
            def limit(self,*a):return self
            async def to_list(self,*a):return []
        self.db.messages.find=lambda *a:Cursor()
        provider=AsyncMock(return_value=Stream(json.dumps(MAP)))
        route=namespace(provider)
        class Response:
            def __init__(self,body,**kwargs):self.body_iterator=body
        credit=AsyncMock(return_value={'deducted':2,'balance':98})
        async def slow_analytics(*args):await asyncio.Event().wait()
        route.update({'StreamingResponse':Response,'db':self.db,'get_current_user':self.ns['get_current_user'],
          'ensure_credits':AsyncMock(),'get_user_plan':AsyncMock(return_value={'id':'free'}),
          'build_routing_decision':lambda *a,**k:{'category':'C','model':'fixture','max_tokens':3500},
          'get_verified_chapters':lambda *a:[],'find_kb_answer':AsyncMock(return_value=None),
          'get_student_profile':AsyncMock(return_value={}), 'build_compact_memory':lambda p:{},
          '_get_mapped_nios_math_context':AsyncMock(return_value='Fractions: numerator and denominator.'),
          '_compact_visual_source':lambda text,limit:text,'_NIOS_DETAIL_RE':re.compile('detail'),
          '_build_nios_system_prompt':lambda *a:'Use chapter JSON schema.',
          'deduct_credits_for_chat':credit,'increment_usage':slow_analytics,'record_token_usage':AsyncMock()})
        # Use an actual diagram request through the actual stream handler and job worker.
        content='Visualize: Mind map for Fractions\n\n[MINDMAP INSTRUCTIONS]'
        self.db.visual_jobs.rows[0]['request_content']=content
        async def response(job, request):
            request.state.visual_job_id=job['job_id']
            return await route['send_message']('s',NS(content=job['request_content']),request)
        self.ns['_visual_response']=response
        await asyncio.wait_for(self.ns['_run'](job['job_id'],self.request),1)
        result=await self.ns['get_visual_job'](job['job_id'],self.request)
        self.assertEqual(result['status'],'completed');credit.assert_awaited_once();provider.assert_awaited_once()
        await self.ns['_run'](job['job_id'],self.request)
        credit.assert_awaited_once();self.assertEqual(len(self.db.messages.rows),2)
        self.assertEqual(result['receipt']['credits_used'],2)
        tasks=list(route.get('_ACTIVITY_TASKS',set()))
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)

    async def test_credit_failure_creates_no_job(self):
        self.ns['ensure_credits'].side_effect=HTTPException(402,'Insufficient credits')
        with self.assertRaises(HTTPException):await self.ns['create_visual_job']('s',self.body,self.request)
        self.assertEqual(self.db.visual_jobs.rows,[])

if __name__=='__main__':unittest.main()
