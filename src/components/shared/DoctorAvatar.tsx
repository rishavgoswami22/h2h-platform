'use client';

import Image from 'next/image';
import { cn } from '@/lib/utils';
import { resolveDoctorAvatar } from '@/constants/doctor-avatars';

const SIZE_PX = {
  sm: 48,
  md: 56,
  lg: 64,
  xl: 80,
} as const;

type DoctorAvatarProps = {
  name: string;
  email?: string | null;
  avatar?: string | null;
  size?: keyof typeof SIZE_PX;
  className?: string;
  imageClassName?: string;
  border?: boolean;
};

export function DoctorAvatar({
  name,
  email,
  avatar,
  size = 'md',
  className,
  imageClassName,
  border = false,
}: DoctorAvatarProps) {
  const px = SIZE_PX[size];
  const profile = resolveDoctorAvatar({ name, email, avatar });
  const isRemote = profile.src.startsWith('http');

  return (
    <div
      className={cn(
        'relative shrink-0 overflow-hidden rounded-full bg-gray-100',
        border && 'ring-2 ring-cyan-200',
        className
      )}
      style={{ width: px, height: px }}
    >
      <Image
        src={profile.src}
        alt={name}
        fill
        sizes={`${px}px`}
        className={cn('object-cover', imageClassName)}
        style={{ objectPosition: profile.objectPosition ?? 'center top' }}
        unoptimized={profile.unoptimized ?? isRemote}
      />
    </div>
  );
}
