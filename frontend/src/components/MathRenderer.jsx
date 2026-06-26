import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

/**
 * MathRenderer — parses text containing LaTeX math notation and renders it.
 *
 * Supports:
 *   $formula$       → inline math (only when content looks like LaTeX)
 *   $$formula$$     → block/display math
 *   ( \formula )    → auto-converted to inline math (AI sometimes uses this pattern)
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
 * Pre-process text: convert ( \latex ) patterns → $\latex$
 * These are emitted by some AI models that use parentheses as math delimiters.
 */
function preprocessMath(text) {
  // Convert ( \frac{a}{b} ) and similar ( \command{} ) patterns to $...$
  return text.replace(/\(\s*(\\[^)]{1,200})\s*\)/g, (_, inner) => `$${inner.trim()}$`);
}

/**
 * Check if a string looks like actual LaTeX math (not currency/plain numbers).
 * Must contain at least one LaTeX indicator: \, ^, _, {, }
 */
function isLaTeXContent(str) {
  return /[\\^_{}\|]/.test(str);
}

/**
 * Parse text and split into segments: plain text, inline math, block math.
 */
function parseSegments(text) {
  // Pre-process to convert ( \formula ) → $\formula$
  const processed = preprocessMath(text);

  const segments = [];
  // Match $$...$$ first (block), then $...$ (inline)
  const regex = /\$\$([^$]+)\$\$|\$([^$\n]+)\$/g;
  let lastIdx = 0;
  let match;

  while ((match = regex.exec(processed)) !== null) {
    if (match.index > lastIdx) {
      segments.push({ type: 'text', content: processed.slice(lastIdx, match.index) });
    }
    if (match[1] !== undefined) {
      segments.push({ type: 'block', content: match[1].trim() });
    } else if (match[2] !== undefined) {
      const content = match[2].trim();
      // Only render as math if it contains LaTeX indicators (avoids $10 → $4 mismatches)
      if (isLaTeXContent(content)) {
        segments.push({ type: 'inline', content });
      } else {
        // Treat the whole match as plain text (restore the $ signs)
        segments.push({ type: 'text', content: match[0] });
      }
    }
    lastIdx = match.index + match[0].length;
  }
  if (lastIdx < processed.length) {
    segments.push({ type: 'text', content: processed.slice(lastIdx) });
  }
  return segments;
}

/**
 * MathLine — render a single line with mixed text + math.
 */
export function MathLine({ text }) {
  if (!text) return <span>{text}</span>;
  const hasLaTeX = /\$|\\\w|(?:\(\s*\\)/.test(text);
  if (!hasLaTeX) return <span>{text}</span>;
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

  const hasMath = /\$|\\\w|(?:\(\s*\\)/.test(text);
  if (!hasMath) return <span className={className}>{text}</span>;

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
