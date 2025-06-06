declare module '@hpcc-js/wasm' {
  export const Graphviz: {
    load(): Promise<{
      layout(dot: string, format: string, engine: string): Promise<string>;
    }>;
  };
} 