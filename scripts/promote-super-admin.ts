/**
 * Promote a user to super_admin by email (when setup API says admin already exists).
 * Run: npx tsx scripts/promote-super-admin.ts your@email.com
 */
import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';

dotenv.config({ path: '.env' });
dotenv.config({ path: '.env.local', override: true });

const email = process.argv[2];
if (!email) {
  console.error('Usage: npx tsx scripts/promote-super-admin.ts your@email.com');
  process.exit(1);
}

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

async function main() {
  const { data, error } = await supabase
    .from('users')
    .update({ role: 'super_admin' })
    .eq('email', email)
    .select('email, full_name, role')
    .single();

  if (error) {
    console.error('Failed:', error.message);
    console.error('Make sure the user signed up first at /login (Google or email).');
    process.exit(1);
  }

  console.log('✅ Promoted to super_admin:', data);
  console.log('Login at http://localhost:3000/super-admin/login');
}

main();
