import { ABOUT_IMAGES } from '@/constants/marketing-images';

const FAKE_AVATAR_PATTERNS = [
  '/images/excellence/ccl-cricket',
  'dicebear.com',
  'lorelei/svg',
];

export type DoctorAvatarProfile = {
  src: string;
  objectPosition?: string;
  unoptimized?: boolean;
};

/** Canonical portraits for H2H clinicians (never use stock / event action shots as avatars). */
export const DOCTOR_AVATARS_BY_EMAIL: Record<string, DoctorAvatarProfile> = {
  'sukdebmahanta2@gmail.com': {
    src: ABOUT_IMAGES.foundersGroup,
    objectPosition: 'center 18%',
    unoptimized: true,
  },
  'akshatchouhan83@gmail.com': {
    src: ABOUT_IMAGES.teamAkshat,
    objectPosition: 'center top',
    unoptimized: true,
  },
  '9778570900jitu@gmail.com': {
    src: ABOUT_IMAGES.teamDeepti,
    objectPosition: 'center top',
  },
};

export const DOCTOR_AVATARS_BY_NAME: Record<string, DoctorAvatarProfile> = {
  'Dr. Sukdeb Mahanta': DOCTOR_AVATARS_BY_EMAIL['sukdebmahanta2@gmail.com'],
  'Dr. Akshat Singh Chouhan': DOCTOR_AVATARS_BY_EMAIL['akshatchouhan83@gmail.com'],
  'Dr. Deepti Ranjan Parida': DOCTOR_AVATARS_BY_EMAIL['9778570900jitu@gmail.com'],
};

function isFakeAvatar(url: string | null | undefined): boolean {
  if (!url) return true;
  return FAKE_AVATAR_PATTERNS.some((p) => url.includes(p));
}

export function resolveDoctorAvatar(input: {
  name?: string | null;
  email?: string | null;
  avatar?: string | null;
}): DoctorAvatarProfile {
  const email = input.email?.toLowerCase().trim();
  if (email && DOCTOR_AVATARS_BY_EMAIL[email]) {
    return DOCTOR_AVATARS_BY_EMAIL[email];
  }

  const name = input.name?.trim();
  if (name && DOCTOR_AVATARS_BY_NAME[name]) {
    return DOCTOR_AVATARS_BY_NAME[name];
  }

  if (input.avatar && !isFakeAvatar(input.avatar)) {
    return { src: input.avatar, objectPosition: 'center top' };
  }

  const seed = encodeURIComponent(name || email || 'doctor');
  return {
    src: `https://api.dicebear.com/9.x/lorelei/svg?seed=${seed}&backgroundColor=b6e3f4`,
    objectPosition: 'center',
  };
}

export function resolveDoctorAvatarSrc(input: {
  name?: string | null;
  email?: string | null;
  avatar?: string | null;
}): string {
  return resolveDoctorAvatar(input).src;
}
