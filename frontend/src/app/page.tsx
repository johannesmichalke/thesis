'use client';

import { useState } from 'react';
import Script from 'next/script';
import GraphvizViewer from './components/GraphvizViewer';
import ExampleSolutions from './components/ExampleSolutions';

export default function Home() {
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dotString, setDotString] = useState<string>();
  const [variables, setVariables] = useState<string[]>([]);
  const [exampleSolutions, setExampleSolutions] = useState<any[]>([]);
  const [showHelp, setShowHelp] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [kSolutions, setKSolutions] = useState(3);
  const [forceExpandExample, setForceExpandExample] = useState(false);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setInput(content);
        setKSolutions(3);
        // Use the content directly in the request instead of waiting for state update
        handleBuild([], 3, false, content);
      };
      reader.readAsText(file);
    }
  };

  const handleBuild = async (variableOrder: string[] = [], kOverride?: number, forceExpand?: boolean, formulaOverride?: string) => {
    setLoading(true);
    setError(null);
    setDotString(undefined);
    setExampleSolutions([]);
    if (forceExpand) setForceExpandExample(true);
    try {
      const requestBody = {
        formula: (formulaOverride ?? input).trim(),
        variable_order: variableOrder,
        k_solutions: kOverride ?? kSolutions,
      };

      const response = await fetch('/api/automaton/dot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorText = await response.text();
        const errorMsg = errorText
          .replace(/\t/g, '    ')
          .replace(/ /g, '\u00A0');
        console.log('Error message received:', JSON.stringify(errorMsg));
        setError(errorMsg);
        setForceExpandExample(false);
        return;
      }

      const data = await response.json();
      console.log('API response:', data);
      setDotString(data.dot);
      setVariables(data.variables || []);
      setExampleSolutions(data.example_solutions || []);
      setForceExpandExample(false);
    } catch (err) {
      const errorMsg = (err instanceof Error ? err.message : 'An error occurred')
        .replace(/\t/g, '    ')
        .replace(/ /g, '\u00A0');
      console.log('Error message received:', JSON.stringify(errorMsg));
      setError(errorMsg);
      setForceExpandExample(false);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    if (draggedIndex === null) return;

    const newVariables = [...variables];
    const [draggedItem] = newVariables.splice(draggedIndex, 1);
    newVariables.splice(targetIndex, 0, draggedItem);

    setVariables(newVariables);
    setDraggedIndex(null);
    handleBuild(newVariables);
  };

  const handleFormulaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    setKSolutions(3);
  };

  const handleAddExample = () => {
    setKSolutions((prev) => {
      const next = prev + 1;
      handleBuild(variables, next, true);
      return next;
    });
  };

  return (
    <main className="min-h-screen p-4">
      <Script
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        strategy="beforeInteractive"
      />
      
      <div className="max-w-[90%] mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-center">Presburger Arithmetical Expression to Automaton</h1>
        
        <div className="space-y-4">
          <textarea
            value={input}
            onChange={handleFormulaChange}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                setKSolutions(3);
                handleBuild();
              }
            }}
            placeholder="Enter a Presburger Arithmetical Expression..."
            className="w-full h-32 p-4 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-2xl"
          />
          
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 cursor-pointer">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              Upload Formula
              <input
                type="file"
                accept=".txt"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
            <span className="text-sm text-gray-500">Upload a .txt file containing your formula</span>
          </div>
          
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
            onClick={() => { setKSolutions(3); handleBuild(); }}
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

        {/* Example Solutions and Graph display */}
        {dotString && (
          <>
            <ExampleSolutions
              solutions={exampleSolutions}
              kSolutions={kSolutions}
              onAddExample={handleAddExample}
              loading={loading}
            />
            
            {variables.length > 0 && (
              <div className="flex flex-col gap-2 my-4">
                <span className="font-semibold text-gray-700">Variable order (drag to reorder):</span>
                <div className="flex flex-wrap gap-2">
                  {variables.map((v, i) => (
                    <div
                      key={v}
                      draggable
                      onDragStart={() => handleDragStart(i)}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, i)}
                      className={`px-3 py-2 bg-blue-100 text-blue-800 rounded font-mono border border-blue-200 cursor-move hover:bg-blue-200 transition-colors ${
                        draggedIndex === i ? 'opacity-50' : ''
                      }`}
                    >
                      {v}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="border rounded-lg overflow-hidden">
              <div className="w-full aspect-[3/2]">
                <GraphvizViewer dot={dotString} />
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
