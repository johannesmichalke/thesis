// /app/api/automaton/route.ts (example)
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    // 1️⃣  Parse the incoming JSON only once
    const { formula, variable_order = [] } = await request.json();

    // 2️⃣  Forward it unchanged
    const backendRes = await fetch('http://localhost:8000/automaton/dot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ formula, variable_order }),
    });

    if (!backendRes.ok) {
      const errorText = await backendRes.text();
      return new NextResponse(errorText, {
        status: backendRes.status,
        headers: { 'Content-Type': 'text/plain' },
      });
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error('Proxy failed:', err);
    return NextResponse.json({ error: 'Failed to process automaton' }, { status: 500 });
  }
}