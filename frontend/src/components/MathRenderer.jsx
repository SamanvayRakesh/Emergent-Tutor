import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

/**
 * MathRenderer — parses text containing LaTeX math notation and renders it.
 *
 * Supports:
 *   $formula$       → inline math
 *   $$formula$$     → block/display math
 *   \frac{a}{b}     → rendered as fraction
 *   x^2, x_n        → superscript/subscript
 *   \sqrt{x}        → square root
 */

function safeRenderInline(latex) {
  try {
    return <InlineMath math={latex} />;
  } catch {
    return <code className="text-yellow-300 bg-black/30 px-1 rounded text-sm">{latex}</code>;
  }
}

function safeRenderBlock(latex) {
  try {
    return <BlockMath math={latex} />;
  } catch {
    return <pre className="text-yellow-300 bg-black/30 p-2 rounded text-sm overflow-x-auto">{latex}</pre>;
  }
}

/**
 * Parse text and split into segments: plain text, inline math, block math.
 */
function parseSegments(text) {
  const segments = [];
  // Match $$...$$ first (block), then $...$ (inline)
  const regex = /\$\$([^$]+)\$\$|\$([^$\n]+)\$/g;
  let lastIdx = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Text before this match
    if (match.index > lastIdx) {
      segments.push({ type: 'text', content: text.slice(lastIdx, match.index) });
    }
    if (match[1] !== undefined) {
      segments.push({ type: 'block', content: match[1].trim() });
    } else if (match[2] !== undefined) {
      segments.push({ type: 'inline', content: match[2].trim() });
    }
    lastIdx = match.index + match[0].length;
  }
  // Remaining text
  if (lastIdx < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIdx) });
  }
  return segments;
}

/**
 * MathLine — render a single line with mixed text + math.
 */
export function MathLine({ text }) {
  if (!text || (!text.includes('$') && !text.includes('\\frac') && !text.includes('\\sqrt'))) {
    return <span>{text}</span>;
  }
  const segments = parseSegments(text);
  return (
    <span>
      {segments.map((seg, i) => {
        if (seg.type === 'block')  return <span key={i} className="block my-2">{safeRenderBlock(seg.content)}</span>;
        if (seg.type === 'inline') return <span key={i}>{safeRenderInline(seg.content)}</span>;
        return <span key={i}>{seg.content}</span>;
      })}
    </span>
  );
}

/**
 * MathText — full text block with math rendering. Handles multi-line content.
 */
export function MathText({ text, className = '' }) {
  if (!text) return null;

  const hasMath = text.includes('$') || text.includes('\\frac') || text.includes('\\sqrt')
    || text.includes('\\times') || text.includes('\\div');

  if (!hasMath) return <span className={className}>{text}</span>;

  // Split by newlines, render each line
  const lines = text.split('\n');
  return (
    <span className={className}>
      {lines.map((line, i) => (
        <span key={i}>
          <MathLine text={line} />
          {i < lines.length - 1 && <br />}
        </span>
      ))}
    </span>
  );
}

export default MathText;
