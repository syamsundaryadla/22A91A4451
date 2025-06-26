import { NextRequest, NextResponse } from 'next/server';
import { Log } from '../../logging-middleware/index';

// In-memory store for URL mappings (for demo; use DB in production)
export const urlMap: Record<string, string> = {};

function generateShortCode(length = 6) {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = '';
  for (let i = 0; i < length; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

export async function POST(req: NextRequest) {
  try {
    const { longUrl } = await req.json();
    if (!longUrl || typeof longUrl !== 'string') {
      await Log('frontend', 'warn', 'api', 'Invalid longUrl received');
      return NextResponse.json({ error: 'Invalid URL' }, { status: 400 });
    }
    const code = generateShortCode();
    urlMap[code] = longUrl;
    const shortUrl = `${req.nextUrl.origin}/api/${code}`;
    await Log('frontend', 'info', 'api', `Shortened ${longUrl} to ${shortUrl}`);
    return NextResponse.json({ shortUrl });
  } catch (err: any) {
    await Log('frontend', 'error', 'api', `Error in shorten API: ${err.message}`);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// For demo: expose the map for GET (not for production)
export async function GET() {
  return NextResponse.json(urlMap);
} 