import { NextRequest, NextResponse } from 'next/server';
import { Log } from '../../../logging-middleware/index';
import { urlMap } from '../shorten';

export async function GET(req: NextRequest, { params }: { params: { code: string } }) {
  const { code } = params;
  const longUrl = urlMap[code];
  if (longUrl) {
    await Log('frontend', 'info', 'api', `Redirecting code ${code} to ${longUrl}`);
    return NextResponse.redirect(longUrl);
  } else {
    await Log('frontend', 'warn', 'api', `Short code not found: ${code}`);
    return NextResponse.json({ error: 'Short URL not found' }, { status: 404 });
  }
} 