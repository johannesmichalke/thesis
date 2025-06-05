'use client';

import { useState } from 'react';
import Script from 'next/script';

export default function Home() {
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [pdfURL, setPdfURL] = useState<string>();
  const [variables, setVariables] = useState<string[]>([]);
  const [showHelp, setShowHelp] = useState(false);

  const handleBuild = async () => {
    setLoading(true);
    setError(null);
    setVariables([]);
    setPdfURL(undefined);
    
    try {
      const response = await fetch('/api/automaton', {
        method: 'POST',
        headers: {
          'Content-Type': 'text/plain',
        },
        body: input,
      });

      if (!response.ok) {
        const errorText = await response.text();
        const errorMsg = errorText
          .replace(/\t/g, '    ')
          .replace(/ /g, '\u00A0');
        console.log('Error message received:', JSON.stringify(errorMsg));
        setError(errorMsg);
        return;
      }

      const data = await response.json();
      // Decode base64 PDF
      const byteCharacters = atob(data.pdf_base64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      setPdfURL(URL.createObjectURL(blob));
      setVariables(data.variables || []);
    } catch (err) {
      const errorMsg = (err instanceof Error ? err.message : 'An error occurred')
        .replace(/\t/g, '    ')
        .replace(/ /g, '\u00A0');
      console.log('Error message received:', JSON.stringify(errorMsg));
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8">
      <Script
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        strategy="beforeInteractive"
      />
      
      <div className="max-w-4xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-center">Presburger Arithmetical Expression to Automaton</h1>
        
        <div className="space-y-4">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleBuild();
              }
            }}
            placeholder="Enter a Presburger Arithmetical Expression..."
            className="w-full h-32 p-4 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-2xl"
          />
          
          {/* Help Section */}
          <div className="mt-2">
            <button
              type="button"
              className="text-blue-600 underline text-sm focus:outline-none"
              onClick={() => setShowHelp((prev) => !prev)}
              aria-expanded={showHelp}
              aria-controls="formula-help-section"
            >
              {showHelp ? 'Hide syntax help' : 'Need help with the syntax?'}
            </button>
            {showHelp && (
              <div
                id="formula-help-section"
                className="mt-2 p-4 bg-gray-50 border border-gray-200 rounded text-sm text-gray-800"
              >
                <div className="mb-2 font-semibold">Formula Syntax Help</div>
                <div className="mb-2">
                  <span className="font-semibold">Boolean connectives:</span><br />
                  <span className="font-mono">AND</span>, <span className="font-mono">OR</span>, <span className="font-mono">NOT</span>, <span className="font-mono">-&gt;</span>, <span className="font-mono">&lt;-&gt;</span><br />
                  <span className="text-gray-600">Example: <span className="font-mono">(x = y) AND (NOT (x &lt; 3))</span></span>
                </div>
                <div className="mb-2">
                  <span className="font-semibold">Quantifiers:</span><br />
                  <span className="font-mono">EX x. ...</span> (there exists), <span className="font-mono">ALL y. ...</span> (for all)<br />
                  <span className="text-gray-600">Example: <span className="font-mono">EX z. x = 4z</span>, <span className="font-mono">ALL y. y &lt;= x</span></span>
                </div>
                <div className="mb-2">
                  <span className="font-semibold">Comparisons:</span><br />
                  <span className="font-mono">=</span>, <span className="font-mono">&lt;=</span>, <span className="font-mono">&lt;</span>, <span className="font-mono">&gt;=</span>, <span className="font-mono">&gt;</span><br />
                  <span className="text-gray-600">Example: <span className="font-mono">x = y + 2</span>, <span className="font-mono">3z &lt; y</span></span>
                </div>
                <div className="mb-2">
                  <span className="font-semibold">Arithmetic:</span><br />
                  <span className="font-mono">x + y</span>, <span className="font-mono">2x + 3</span><br />
                  <span className="text-gray-600">Example: <span className="font-mono">x = y + 2</span>, <span className="font-mono">2x + 3</span></span>
                </div>
                <div className="mb-2">
                  <span className="font-semibold">Full formula examples:</span><br />
                  <span className="block font-mono bg-gray-100 rounded p-2 my-1">x = y + 2</span>
                  <span className="block font-mono bg-gray-100 rounded p-2 my-1">EX z. x = 4z</span>
                  <span className="block font-mono bg-gray-100 rounded p-2 my-1">ALL y. y &lt;= x</span>
                  <span className="block font-mono bg-gray-100 rounded p-2 my-1">(x = y) AND (NOT (x &lt; 3))</span>
                  <span className="block font-mono bg-gray-100 rounded p-2 my-1">EX x. (x &lt; 3) -&gt; (y = x + 2)</span>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  <span className="font-semibold">Grammar:</span><br />
                  <pre className="whitespace-pre-wrap font-mono text-xs bg-gray-100 rounded p-2 mt-1">{`
?start: formula
?formula: implication
?implication: equivalence | equivalence "->" implication  -> implies
?equivalence: or_expr | or_expr "<->" equivalence         -> iff
?or_expr: and_expr | or_expr "OR" and_expr                -> or_expr
?and_expr: not_expr | and_expr "AND" not_expr             -> and_expr
?not_expr: "NOT" atom -> not_expr | atom
?atom: comparison | quantifier | "(" formula ")"
?quantifier: EX VAR "." formula -> ex_quantifier | ALL VAR "." formula -> all_quantifier
?comparison: term "<=" term -> leq | term "=" term -> eq | term "<" term -> less | term ">" term -> greater | term ">=" term -> greater_equal
?term: sum
?sum: product | sum "+" product -> add
?product: CONST VAR -> mult | factor
?factor: VAR -> var | CONST -> const
VAR: /[a-z][a-z0-9_]*/i
CONST: /[0-9]+/
`}</pre>
                </div>
              </div>
            )}
          </div>
          
          <button
            onClick={handleBuild}
            disabled={loading}
            className="w-full py-2 px-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Building...' : 'Build Automaton'}
          </button>
        </div>

        {error && (
          <pre
            className="p-4 bg-red-100 text-red-700 rounded-lg whitespace-pre-wrap font-mono"
            style={{ fontFamily: 'JetBrains Mono, Fira Mono, Menlo, Consolas, monospace', fontSize: '16px' }}
          >
            {error}
          </pre>
        )}

        {/* PDF and variables display */}
        {pdfURL && (
          <>
            {variables.length > 0 && (
              <div className="flex items-center gap-2 my-4">
                <span className="font-semibold text-gray-700">Variable order from top to bottom:</span>
                {variables.map((v, i) => (
                  <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-mono border border-blue-200">
                    {v}
                  </span>
                ))}
              </div>
            )}
            <div className="border rounded-lg overflow-hidden">
              <object data={pdfURL} type="application/pdf" width="100%" height="600">
                <p>
                  Your browser cant display embedded PDFs.
                  <a href={pdfURL} className="text-blue-500 hover:text-blue-600 ml-2">Download it instead.</a>
                </p>
              </object>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
