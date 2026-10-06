"""Validate structured tutor cards. Never execute AI-generated code."""
import json, re

BLOCK_RE = re.compile(r'\[(CHECK)\]([\s\S]*?)\[/\1\]')

def clean_text(value, limit=240):
    return value.strip()[:limit] if isinstance(value, str) else ''

def extract_cards(content):
    checks = []
    def replace(match):
        try: data = json.loads(match[2])
        except (ValueError, TypeError): return '\n[This learning card could not be displayed.]\n'
        if isinstance(data, dict) and len(checks) < 1:
            options = data.get('options')
            question = clean_text(data.get('question'), 500)
            if question and isinstance(options, list) and len(options) == 4 and all(clean_text(o) for o in options) and data.get('correct') in ('A', 'B', 'C', 'D'):
                checks.append({'question': question, 'options': [clean_text(o) for o in options], 'correct': data['correct'], 'explanation': clean_text(data.get('explanation'), 800)})
                return '\n'
        return '\n[This learning card could not be displayed.]\n'
    content = BLOCK_RE.sub(replace, content)
    # Suppress truncated structured output rather than exposing answers/JSON.
    content = re.sub(r'\[(CHECK)\][\s\S]*$', '\n[The learning card was interrupted. Ask for a quick quiz again.]', content)
    return content.strip(), checks
