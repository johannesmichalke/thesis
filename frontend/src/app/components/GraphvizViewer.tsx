'use client';

import React, { useEffect, useState } from 'react';
import { Graphviz } from '@hpcc-js/wasm';

export default function GraphvizViewer({ dot }: { dot: string }) {
  const [svg, setSvg] = useState<string | null>(null);

  useEffect(() => {
    const renderGraph = async () => {
      try {
        const graphviz = await Graphviz.load();
        const svgStr = await graphviz.layout(dot, "svg", "dot");
        // Add viewBox and preserveAspectRatio to the SVG
        const modifiedSvg = svgStr.replace('<svg', '<svg preserveAspectRatio="xMidYMid meet" style="width: 100%; height: 100%;"');
        setSvg(modifiedSvg);
      } catch (err) {
        console.error('Error rendering graph:', err);
      }
    };

    renderGraph();
  }, [dot]);

  return (
    <div className="w-full h-full flex items-center justify-center">
      <div
        dangerouslySetInnerHTML={{ __html: svg ?? 'Loading graph...' }}
        className="w-full h-full"
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      />
    </div>
  );
} 