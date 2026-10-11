import ast,asyncio,json,re,logging,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
sourcecode=(Path(__file__).resolve().parents[1]/'routes'/'chat.py').read_text();tree=ast.parse(sourcecode)
names={'_normal_title','_study_visual_schema','_normalize_study_reply','_validate_study_reply','_study_group_excerpt','_generate_study_batches'}
class Stream:
 def __init__(self,raw):self.raw=raw;self.closed=False
 def __aiter__(self):return self.iterate()
 async def iterate(self):yield NS(choices=[NS(delta=NS(content=self.raw),finish_reason='stop')])
 async def close(self):self.closed=True
class Tests(unittest.IsolatedAsyncioTestCase):
 async def test_later_group_retry_and_failure(self):
  def reply(topics):return '[STUDYVISUAL]'+json.dumps({'kind':'cheatsheet','title':'Chapter','summary':'Chapter essentials.','sections':[{'heading':t,'type':'concept','items':[{'label':'Definition','detail':'A grounded definition.'},{'label':'Example','detail':'A grounded example.'}]} for t in topics]})+'[/STUDYVISUAL]'
  topics=['One','Two','Three','Four','Five','Six','Seven'];source={'topics':topics,'text':'Textbook fixture.','complete':True}
  for fail in [False,True]:
   streams=[Stream(reply(topics[:3])),Stream('{broken'),Stream('{still broken' if fail else reply(topics[3:6])),Stream(reply(topics[6:]))]
   provider=AsyncMock(side_effect=streams)
   ns={'asyncio':asyncio,'json':json,'re':re,'logger':logging.getLogger('test'),'_VISUAL_TYPES':{'concept','compare','formula','steps','cycle','timeline'},'openai_client':NS(chat=NS(completions=NS(create=provider)))}
   exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names],type_ignores=[]),'batches','exec'),ns)
   events=[]
   try:
    async for e in ns['_generate_study_batches']([{'role':'system','content':'Grounded schema.'},{'role':'user','content':'Chapter'}],'cheatsheet',source,'fixture',30000,asyncio.get_running_loop().time()+20):events.append(e)
   except (ValueError,json.JSONDecodeError):self.assertTrue(fail)
   self.assertEqual(events[0]['type'],'visual_partial');first=json.loads(events[0]['content'][13:-14]);self.assertEqual(len(first['sections']),3);self.assertEqual(first['coverage']['status'],'partial')
   if fail:self.assertEqual(len(events),1);self.assertEqual(provider.await_count,3)
   else:
    self.assertEqual(events[-1]['type'],'visual_ready');final=json.loads(events[-1]['content'][13:-14]);self.assertEqual([s['heading']for s in final['sections']],topics);self.assertEqual(final['coverage']['status'],'complete');self.assertEqual(provider.await_count,4)
   self.assertTrue(all(s.closed for s in streams[:provider.await_count]))
 async def test_budget_deadline_and_source_scope(self):
  provider=AsyncMock()
  ns={'asyncio':asyncio,'json':json,'re':re,'logger':logging.getLogger('test'),'_VISUAL_TYPES':{'concept','compare','formula','steps','cycle','timeline'},'openai_client':NS(chat=NS(completions=NS(create=provider)))}
  exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names],type_ignores=[]),'batches','exec'),ns)
  text='Chapter introduction\n1.1 One\nFirst fact.\n1.2 Two\nSecond fact.\n1.3 Three\nThird fact.'
  excerpt=ns['_study_group_excerpt'](text,['Two']);self.assertIn('Second fact',excerpt);self.assertNotIn('First fact',excerpt);self.assertNotIn('Third fact',excerpt)
  self.assertEqual(ns['_study_group_excerpt']('Unnumbered source',['Two']),'Unnumbered source')
  source={'topics':['Two'],'text':text,'complete':True};messages=[{'role':'system','content':'Schema'},{'role':'user','content':'Chapter'}]
  for budget,deadline,error in [(100,asyncio.get_running_loop().time()+10,ValueError),(30000,asyncio.get_running_loop().time()-1,asyncio.TimeoutError)]:
   with self.assertRaises(error):
    async for event in ns['_generate_study_batches'](messages,'cheatsheet',source,'fixture',budget,deadline):self.fail('An exhausted request must not emit a complete visual')
  provider.assert_not_awaited()
if __name__=='__main__':unittest.main()
