/** Patch clinician avatar URLs in Supabase (no full reseed). */
import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';

dotenv.config({ path: '.env' });
dotenv.config({ path: '.env.local', override: true });

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

const AVATARS: Record<string, string> = {
  'sukdebmahanta2@gmail.com': '/images/about/founders-group.webp',
  'akshatchouhan83@gmail.com': '/images/about/dr-akshat-chouhan.webp',
  '9778570900jitu@gmail.com': '/images/about/team-deepti.webp',
};

async function main() {
  for (const [email, avatar_url] of Object.entries(AVATARS)) {
    const { error } = await supabase.from('users').update({ avatar_url }).eq('email', email);
    if (error) console.error(`❌ ${email}:`, error.message);
    else console.log(`✅ ${email} → ${avatar_url}`);
  }
}

main();
