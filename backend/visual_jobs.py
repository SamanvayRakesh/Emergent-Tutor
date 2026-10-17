"""Recoverable visual generation. HTTP polling is independent of model streams."""
import asyncio
import hashlib
import json
import re
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from core import db, logger, get_current_user
from credits import ensure_credits
from models import ChatMessageRequest

router = APIRouter()
_TASKS = {}
_TERMINAL = {'completed', 'failed', 'cancelled'}

class VisualJobRequest(BaseModel):
    content: str = Field(min_length=1, max_length=24000)
    request_id: str = Field(min_length=12, max_length=96)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _public(job):
    return {key: job.get(key) for key in (
        'job_id', 'session_id', 'status', 'request_content', 'content', 'ready',
        'total_topics', 'error', 'receipt', 'created_at', 'updated_at')}

async def _saved_result(job):
    """Never regenerate or charge again if the previous worker saved the answer."""
    saved = await db.messages.find_one({'visual_job_id': job['job_id'], 'role': 'assistant',
                                       'session_id': job['session_id']}, {'_id': 0})
    if not saved:
        return None
    receipt = saved.get('receipt') or {'message_id': saved.get('message_id'), 'receipt_confirmed': False}
    update = {'status': 'completed', 'content': saved['content'], 'ready': True,
              'receipt': receipt, 'error': None, 'updated_at': _now()}
    await db.visual_jobs.update_one({'_id': job['job_id']}, {'$set': update})
    return {**job, **update}

async def _visual_response(job, request):
    from routes.chat import send_message
    request.state.visual_job_id = job['job_id']
    return await send_message(job['session_id'], ChatMessageRequest(content=job['request_content']), request)

async def _consume(job, request):
    response = await _visual_response(job, request)
    iterator = response.body_iterator
    try:
        async for raw in iterator:
            payload = raw.decode() if isinstance(raw, bytes) else raw
            data_lines = [line[5:].lstrip() for line in payload.splitlines() if line.startswith('data:')]
            if not data_lines:
                continue
            event = json.loads('\n'.join(data_lines))
            current = await db.visual_jobs.find_one({'_id': job['job_id']}, {'status': 1})
            if not current or current['status'] == 'cancelled':
                return
            kind = event.get('type')
            update = {'updated_at': _now()}
            if kind == 'accepted':
                update['total_topics'] = event.get('total_topics')
            elif kind in ('visual_partial', 'visual_ready'):
                update.update(content=event['content'], ready=kind == 'visual_ready')
            elif kind == 'done':
                update.update(status='completed', ready=True, receipt=event, error=None)
            elif kind == 'error':
                update.update(status='failed', error={'code': event.get('code'), 'message': event.get('message')})
            await db.visual_jobs.update_one({'_id': job['job_id'], 'status': 'running'}, {'$set': update})
            if kind in ('done', 'error'):
                return
        # A dropped generator must not silently strand a running job.
        recovered = await _saved_result(job)
        if not recovered:
            raise RuntimeError('Visual worker ended before completion')
    finally:
        close = getattr(iterator, 'aclose', None)
        if close:
            await close()

async def _run(job_id, request):
    # Mongo's atomic state transition prevents duplicate workers across processes.
    claim = await db.visual_jobs.update_one({'_id': job_id, 'status': 'queued'},
                                            {'$set': {'status': 'running', 'updated_at': _now()}})
    if not claim.modified_count:
        return
    job = await db.visual_jobs.find_one({'_id': job_id})
    try:
        if await _saved_result(job):
            return
        # Persist the user request once, before source/model preparation begins.
        await db.messages.update_one({'_id': job_id + ':user'}, {'$setOnInsert': {
            'session_id': job['session_id'], 'role': 'user', 'content': job['request_content'],
            'visual_job_id': job_id, 'timestamp': job['created_at']}}, upsert=True)
        await asyncio.wait_for(_consume(job, request), timeout=225)
    except asyncio.CancelledError:
        await db.visual_jobs.update_one({'_id': job_id, 'status': 'running'},
                                        {'$set': {'status': 'cancelled', 'updated_at': _now()}})
        raise
    except Exception as exc:
        logger.exception('Visual job %s failed', job_id)
        if await _saved_result(job):
            return
        detail = getattr(exc, 'detail', None)
        message = detail.get('message') if isinstance(detail, dict) else detail if isinstance(detail, str) else None
        await db.visual_jobs.update_one({'_id': job_id, 'status': 'running'}, {'$set': {
            'status': 'failed', 'updated_at': _now(), 'error': {
                'code': 'VISUAL_JOB_FAILED', 'message': message or
                'This visual could not finish. Completed topics are kept; retry when the service is available.'}}})

def _schedule(job_id, request):
    if job_id in _TASKS:
        return
    task = asyncio.create_task(_run(job_id, request))
    _TASKS[job_id] = task
    def finished(done):
        _TASKS.pop(job_id, None)
        if not done.cancelled() and done.exception():
            exc = done.exception()
            logger.error('Visual job task failed', exc_info=(type(exc), exc, exc.__traceback__))
    task.add_done_callback(finished)

async def _owned(job_id, request):
    user = await get_current_user(request)
    job = await db.visual_jobs.find_one({'_id': job_id, 'user_id': user['user_id']})
    if not job:
        raise HTTPException(status_code=404, detail='Visual job not found')
    session = await db.chat_sessions.find_one({'session_id': job['session_id'], 'user_id': user['user_id']})
    if not session or session.get('class_level') != user.get('class_level'):
        raise HTTPException(status_code=403, detail='This chapter is outside your active grade')
    return job

@router.post('/chat/sessions/{session_id}/visual-jobs', status_code=202)
async def create_visual_job(session_id: str, body: VisualJobRequest, request: Request):
    user = await get_current_user(request)
    session = await db.chat_sessions.find_one({'session_id': session_id, 'user_id': user['user_id']})
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    if session.get('class_level') != user.get('class_level'):
        raise HTTPException(status_code=403, detail='This chapter is outside your active grade')
    if not re.fullmatch(r'[A-Za-z0-9_-]{12,96}', body.request_id):
        raise HTTPException(status_code=400, detail='Invalid request ID')
    match = re.match(r'^Visualize: (Mind map|Flowchart|Graph|PDF Cheat Sheet|Revision Notes|Key Points|Quick Revision) for ', body.content)
    tag = 'MINDMAP' if match and match[1] == 'Mind map' else 'FLOWCHART' if match and match[1] == 'Flowchart' else 'STUDYVISUAL'
    if not match or f'[{tag} INSTRUCTIONS]' not in body.content:
        raise HTTPException(status_code=422, detail='Choose a supported chapter visual format')
    identity = '\0'.join((user['user_id'], session_id, body.request_id))
    job_id = 'vjob_' + hashlib.sha256(identity.encode()).hexdigest()[:40]
    existing = await db.visual_jobs.find_one({'_id': job_id})
    if existing:
        if existing['request_content'] != body.content:
            raise HTTPException(status_code=409, detail='Request ID already belongs to another visual')
        if existing['status'] == 'queued':
            _schedule(job_id, request)
        return _public(existing)
    await ensure_credits(user['user_id'], 'ai_message')
    now = _now()
    doc = {'job_id': job_id, 'user_id': user['user_id'], 'session_id': session_id,
           'request_content': body.content, 'status': 'queued', 'content': '', 'ready': False,
           'total_topics': None, 'error': None, 'receipt': None, 'created_at': now, 'updated_at': now}
    await db.visual_jobs.update_one({'_id': job_id}, {'$setOnInsert': doc}, upsert=True)
    _schedule(job_id, request)
    return _public(await db.visual_jobs.find_one({'_id': job_id}))

@router.get('/chat/visual-jobs/{job_id}')
async def get_visual_job(job_id: str, request: Request):
    job = await _owned(job_id, request)
    if job['status'] == 'queued':
        _schedule(job_id, request)
    if job['status'] not in _TERMINAL:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(job['updated_at'])).total_seconds()
        if age > 240:
            recovered = await _saved_result(job)
            if recovered:
                job = recovered
            else:
                update = {'status': 'failed', 'updated_at': _now(), 'error': {
                    'code': 'WORKER_INTERRUPTED', 'message': 'Generation was interrupted on the server. Finished topics remain available. Please retry.'}}
                await db.visual_jobs.update_one({'_id': job_id, 'status': job['status']}, {'$set': update})
                job = {**job, **update}
    return _public(job)

@router.post('/chat/visual-jobs/{job_id}/cancel')
async def cancel_visual_job(job_id: str, request: Request):
    job = await _owned(job_id, request)
    if job['status'] not in _TERMINAL:
        saved = await _saved_result(job)
        if saved:
            return _public(saved)
        await db.visual_jobs.update_one({'_id': job_id, 'status': {'$in': ['queued', 'running']}},
                                        {'$set': {'status': 'cancelled', 'updated_at': _now()}})
        task = _TASKS.get(job_id)
        if task:
            task.cancel()
    return _public(await db.visual_jobs.find_one({'_id': job_id}))

@router.post('/chat/sessions/{session_id}/visual-jobs/cancel')
async def cancel_visual_request(session_id: str, body: VisualJobRequest, request: Request):
    """Stop safely even if the create response was lost before the client saw a job ID."""
    user = await get_current_user(request)
    session = await db.chat_sessions.find_one({'session_id': session_id, 'user_id': user['user_id']})
    if not session or session.get('class_level') != user.get('class_level'):
        raise HTTPException(status_code=403, detail='Chapter access denied')
    if not re.fullmatch(r'[A-Za-z0-9_-]{12,96}', body.request_id):
        raise HTTPException(status_code=400, detail='Invalid request ID')
    identity = '\0'.join((user['user_id'], session_id, body.request_id))
    job_id = 'vjob_' + hashlib.sha256(identity.encode()).hexdigest()[:40]
    now = _now()
    await db.visual_jobs.update_one({'_id': job_id}, {'$setOnInsert': {
        'job_id': job_id, 'user_id': user['user_id'], 'session_id': session_id,
        'request_content': body.content, 'status': 'cancelled', 'content': '', 'ready': False,
        'total_topics': None, 'error': None, 'receipt': None, 'created_at': now, 'updated_at': now}}, upsert=True)
    return await cancel_visual_job(job_id, request)
