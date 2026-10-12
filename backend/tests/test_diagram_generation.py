"""Credential-free regression tests for structured diagrams and quota errors."""
import ast,asyncio,json,re,logging,unittest,uuid
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
source=(Path(__file__).resolve().parents[1]/'routes'/'chat.py').read_text();tree=ast.parse(source)
class Stream:
 def __init__(self,raw,reason='stop'):self.raw=raw;self.reason=reason;self.closed=False
 def __aiter__(self):return self.iterate()
 async def iterate(self):yield NS(choices=[NS(delta=NS(content=self.raw),finish_reason=self.reason)])
 async def close(self):self.closed=True
class ProviderError(Exception):
 def __init__(self,status,message):self.status_code=status;super().__init__(message)
class HTTPException(Exception):
 def __init__(self,status_code,detail):self.status_code=status_code;self.detail=detail
MAP={'title':'Fractions','summary':'Parts of a whole.','branches':[{'label':'Numerator','relation':'counts','points':['The selected parts.']},{'label':'Denominator','relation':'counts','points':['Equal parts in the whole.']}]}
FLOW={'title':'Solve a fraction problem','summary':'A learning sequence.','steps':[{'label':'Read','detail':'Read the quantities.'},{'label':'Solve','detail':'Apply the relevant operation.'}]}
def namespace(provider):
 ns={'uuid':uuid,'json':json,'re':re,'asyncio':asyncio,'datetime':datetime,'timezone':timezone,'logger':logging.getLogger('diagram-tests'),'HTTPException':HTTPException,'openai_client':NS(chat=NS(completions=NS(create=provider)))}
 names={'_diagram_schema','_normalize_diagram_reply','_generate_diagram','send_message'}
 nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
 for n in nodes:
  n.decorator_list=[];n.returns=None
  for arg in n.args.args:arg.annotation=None
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'diagrams','exec'),ns);return ns
class Tests(unittest.IsolatedAsyncioTestCase):
 async def test_truncated_output_retries_then_validates(self):
  raw=json.dumps(MAP);streams=[Stream(raw[:50],'length'),Stream(raw)]
  provider=AsyncMock(side_effect=streams);ns=namespace(provider)
  result,inputs,outputs=await ns['_generate_diagram']([{'role':'system','content':'Grounded JSON schema.'},{'role':'user','content':'Map fractions.'}],'MINDMAP','fixture',20000,asyncio.get_running_loop().time()+20)
  self.assertTrue(result.startswith('[MINDMAP]'));self.assertEqual(json.loads(result[9:-10]),MAP);self.assertEqual(provider.await_count,2);self.assertTrue(all(s.closed for s in streams));self.assertGreater(inputs,0);self.assertGreater(outputs,0)
  self.assertEqual(provider.call_args_list[0].kwargs['response_format']['type'],'json_schema');self.assertTrue(provider.call_args_list[0].kwargs['extra_body']['provider']['require_parameters'])
 async def test_unsupported_schema_fallback_still_validates(self):
  provider=AsyncMock(side_effect=[ProviderError(400,'response_format json_schema unsupported'),ProviderError(400,'response_format json_object unsupported'),Stream(json.dumps(FLOW))]);ns=namespace(provider)
  result,_,_=await ns['_generate_diagram']([{'role':'system','content':'JSON schema.'},{'role':'user','content':'Study path.'}],'FLOWCHART','fixture',20000,asyncio.get_running_loop().time()+20)
  self.assertEqual(json.loads(result[11:-12]),FLOW);self.assertEqual(provider.await_count,3);self.assertNotIn('response_format',provider.call_args.kwargs)
 async def test_malformed_objects_cannot_complete(self):
  provider=AsyncMock(side_effect=[Stream('{bad') for _ in range(3)]);ns=namespace(provider)
  with self.assertRaises(json.JSONDecodeError):await ns['_generate_diagram']([{'role':'system','content':'JSON schema.'},{'role':'user','content':'Map.'}],'MINDMAP','fixture',20000,asyncio.get_running_loop().time()+20)
  with self.assertRaises(ValueError):ns['_normalize_diagram_reply'](json.dumps({**MAP,'branches':[]}), 'MINDMAP')
  self.assertEqual(ns['_normalize_diagram_reply']('[MINDMAP]'+json.dumps(MAP),'MINDMAP'), '[MINDMAP]'+json.dumps(MAP,separators=(',',':'))+'[/MINDMAP]')
 async def test_auth_failure_is_not_downgraded(self):
  provider=AsyncMock(side_effect=ProviderError(401,'Unauthorized'));ns=namespace(provider)
  with self.assertRaises(ProviderError):await ns['_generate_diagram']([{'role':'system','content':'JSON.'},{'role':'user','content':'Map.'}],'MINDMAP','fixture',20000,asyncio.get_running_loop().time()+20)
  self.assertEqual(provider.await_count,1)
 async def test_only_validated_diagrams_are_saved_and_charged(self):
  class Cursor:
   def sort(self,*a):return self
   def limit(self,*a):return self
   async def to_list(self,*a):return []
  class Response:
   def __init__(self,body,**kwargs):self.body_iterator=body
  for valid in [True,False]:
   raw=json.dumps(MAP) if valid else '{malformed'
   provider=AsyncMock(side_effect=[Stream(raw) for _ in range(3)]);ns=namespace(provider)
   session={'class_level':'10','subject':'Mathematics','chapter':'Fractions'}
   messages=NS(insert_one=AsyncMock(),find=lambda *a:Cursor())
   credit=AsyncMock(return_value={'deducted':2,'balance':98})
   ns.update({'StreamingResponse':Response,'db':NS(chat_sessions=NS(find_one=AsyncMock(return_value=session),update_one=AsyncMock()),messages=messages,users=NS(find_one=AsyncMock(return_value={'xp':10,'level':1}),update_one=AsyncMock())),
    'get_current_user':AsyncMock(return_value={'user_id':'u','class_level':'10','school':'nios'}),'ensure_credits':AsyncMock(),'get_user_plan':AsyncMock(return_value={'id':'free'}),'check_budget':AsyncMock(side_effect=AssertionError('Monthly tokens must not gate credited requests')),
    'build_routing_decision':lambda *a,**k:{'category':'C','model':'fixture','max_tokens':3500},'get_verified_chapters':lambda *a:[],'find_kb_answer':AsyncMock(return_value=None),'get_student_profile':AsyncMock(return_value={}), 'build_compact_memory':lambda p:{},
    '_get_mapped_nios_math_context':AsyncMock(return_value='Fractions: numerator and denominator.'),'_compact_visual_source':lambda text,limit:text,'_NIOS_DETAIL_RE':re.compile('detail'), '_build_nios_system_prompt':lambda *a:'Use this chapter JSON schema.',
    'deduct_credits_for_chat':credit,'increment_usage':AsyncMock(),'record_token_usage':AsyncMock()})
   response=await ns['send_message']('s',NS(content='Visualize: Mind map for Fractions\n\n[MINDMAP INSTRUCTIONS]'),None)
   ns['check_budget'].assert_not_awaited()
   events=[json.loads(e[6:]) for e in [e async for e in response.body_iterator] if e.startswith('data:')]
   self.assertEqual(events[0]['type'],'accepted');self.assertFalse(any(e['type']=='chunk' for e in events))
   if valid:
    self.assertEqual([e['type'] for e in events],['accepted','visual_ready','done']);self.assertEqual(messages.insert_one.await_count,2);credit.assert_awaited_once();self.assertEqual(messages.insert_one.call_args.args[0]['content'],events[1]['content'])
   else:self.assertEqual(events[-1]['type'],'error');self.assertEqual(messages.insert_one.await_count,1);credit.assert_not_awaited()
 async def test_insufficient_credits_blocks_before_generation(self):
  provider=AsyncMock();ns=namespace(provider);messages=NS(insert_one=AsyncMock(),insert_many=AsyncMock())
  monthly=AsyncMock(side_effect=AssertionError('No monthly restriction'))
  ns.update({'db':NS(chat_sessions=NS(find_one=AsyncMock(return_value={'class_level':'10'})),messages=messages),'get_current_user':AsyncMock(return_value={'user_id':'u','class_level':'10'}),'ensure_credits':AsyncMock(side_effect=HTTPException(402,{'message':'Not enough credits'})),'get_user_plan':AsyncMock(return_value={'id':'free'}),'check_budget':monthly})
  with self.assertRaises(HTTPException) as caught:await ns['send_message']('s',NS(content='Map fractions.'),None)
  self.assertEqual(caught.exception.status_code,402);monthly.assert_not_awaited();messages.insert_one.assert_not_awaited();messages.insert_many.assert_not_awaited();provider.assert_not_awaited()
if __name__=='__main__':unittest.main()
