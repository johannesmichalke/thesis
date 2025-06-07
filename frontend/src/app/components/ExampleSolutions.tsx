import React from 'react';

interface ExampleSolution {
  path_int: number[];
  path_bits: string[];
  variables: string[];
  var_bits: { [key: string]: string };
  var_ints: { [key: string]: number };
}

interface ExampleSolutionsProps {
  solutions: ExampleSolution[];
  kSolutions: number;
  onAddExample: () => void;
  loading: boolean;
}

export default function ExampleSolutions({ solutions, kSolutions, onAddExample, loading }: ExampleSolutionsProps) {
  if (!solutions || solutions.length === 0) return null;

  // Determine if we should show the + button or the 'no more solutions' card
  const showAddButton = solutions.length === kSolutions;
  const showNoMore = kSolutions > solutions.length;

  // For sizing, use the first solution as a reference
  const referenceSolution = solutions[solutions.length - 1];

  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold mb-4">Example Solutions</h2>
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {solutions.map((solution, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md p-4 border border-gray-200 flex flex-col"
          >
            <div className="mb-2">
              <span className="font-semibold text-gray-700">Solution {index + 1}</span>
            </div>
            {/* Path Information (only show if path_bits is not empty) */}
            {solution.path_bits && solution.path_bits.length > 0 && (
              <div className="mb-2">
                <div className="text-sm font-medium text-gray-600 mb-1">Path (binary):</div>
                <div className="flex flex-wrap items-center gap-1">
                  {solution.path_bits.map((bit, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-mono text-sm"
                    >
                      {bit}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {/* Variable Values */}
            <div>
              <div className="text-sm font-medium text-gray-600 mb-1">Variable Values:</div>
              <div className="grid grid-cols-1 gap-1">
                {solution.variables.map((varName) => (
                  <div key={varName} className="flex flex-col gap-0.5">
                    <div className="font-medium text-gray-700">{varName}:</div>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1">
                        <span className="text-gray-500 text-sm">Binary:</span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-mono text-sm">
                          {solution.var_bits[varName] || 'ε'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-gray-500 text-sm">Integer:</span>
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded font-mono text-sm">
                          {solution.var_ints[varName]}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
        {/* Add Example Button or No More Solutions Card */}
        {showAddButton && referenceSolution && (
          <button
            type="button"
            onClick={onAddExample}
            disabled={loading}
            className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg shadow-md p-4 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-200 transition-colors min-h-[180px]"
            style={{ minHeight: '180px' }}
            aria-label="Generate another example"
          >
            <span className="text-4xl text-gray-400 mb-2">+</span>
            <span className="text-gray-500 font-medium">Generate another example</span>
          </button>
        )}
        {showNoMore && referenceSolution && (
          <div
            className="bg-red-50 border-2 border-dashed border-red-300 rounded-lg shadow-md p-4 flex flex-col items-center justify-center min-h-[180px]"
            style={{ minHeight: '180px' }}
          >
            <span className="text-2xl text-red-400 mb-2">✗</span>
            <span className="text-red-600 font-medium text-center">expression has no more solutions</span>
          </div>
        )}
      </div>
    </div>
  );
} 