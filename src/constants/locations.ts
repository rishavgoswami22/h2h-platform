import { CLINIC_IMAGES, ABOUT_IMAGES } from '@/constants/marketing-images';

export interface Location {
  id: string;
  name: string;
  city: string;
  state: string;
  address: string;
  tier: 1 | 2;
  latitude: number;
  longitude: number;
  phone: string;
  email: string;
  timings: string;
  services: string[];
  facilities: string[];
  image?: string;
}

const H2H_SERVICES = [
  'Pain Relief & Physiotherapy',
  'Advanced Rehabilitation',
  'Sports Performance',
  'Digital Health',
  'Therapeutic Yoga',
  'Nutrition & Lifestyle',
  'Home Visits',
  'Online Consultations',
];

export const DEFAULT_LOCATIONS: Location[] = [
  {
    id: 'kolkata-basdroni',
    name: 'H2H Kolkata — Basdroni',
    city: 'Kolkata',
    state: 'West Bengal',
    address: '275/1 Bidhanpally Road, near Sonali Park, Basdroni, Kolkata - 700084',
    tier: 2,
    latitude: 22.4758,
    longitude: 88.3575,
    phone: '+91 62916 15560',
    email: 'official@healtohealth.in',
    timings: 'Mon-Sat: 9:00 AM - 6:00 PM',
    services: H2H_SERVICES,
    facilities: ['Parking', 'Wheelchair Access', 'Treatment Rooms', 'Rehab Equipment'],
    image: CLINIC_IMAGES.clinicInterior,
  },
  {
    id: 'bhubaneswar-motive',
    name: 'H2H × Motive Physiocare',
    city: 'Bhubaneswar',
    state: 'Odisha',
    address: 'Motive Physiocare & Physical Fitness Clinic, S-4/96, Neeladri Vihar, CS PUR, Bhubaneswar',
    tier: 2,
    latitude: 20.2961,
    longitude: 85.8245,
    phone: '+91 62916 15560',
    email: 'official@healtohealth.in',
    timings: 'Mon-Sat: 9:00 AM - 6:00 PM',
    services: H2H_SERVICES,
    facilities: ['Parking', 'Wheelchair Access', 'Gym', 'Physio Lab'],
    image: CLINIC_IMAGES.physioManualTherapy,
  },
  {
    id: 'online-worldwide',
    name: 'H2H Online',
    city: 'Worldwide',
    state: 'Online',
    address: 'Telehealth — available globally',
    tier: 1,
    latitude: 20.5937,
    longitude: 78.9629,
    phone: '+91 62916 15560',
    email: 'official@healtohealth.in',
    timings: 'Mon-Sun: 9:00 AM - 8:00 PM IST',
    services: ['Tele-Rehabilitation', 'Online Consultations', 'Home Exercise Programs'],
    facilities: ['Video Consultation', 'Digital Health Records'],
    image: ABOUT_IMAGES.homeVisits,
  },
];

export const HOME_VISIT_CITIES = [
  'Kolkata',
  'Delhi',
  'Puri',
  'Bhubaneswar',
  'Mohali',
  'Chandigarh',
  'Zirakpur',
  'Dera Bassi',
  'Indore',
  'Dewas',
  'Dehradun',
] as const;

export const INDIAN_CITIES = [
  { name: 'Kolkata', state: 'West Bengal', tier: 2 },
  { name: 'Bhubaneswar', state: 'Odisha', tier: 2 },
  { name: 'Delhi', state: 'Delhi', tier: 1 },
  { name: 'Puri', state: 'Odisha', tier: 2 },
  { name: 'Mohali', state: 'Punjab', tier: 2 },
  { name: 'Chandigarh', state: 'Chandigarh', tier: 2 },
  { name: 'Indore', state: 'Madhya Pradesh', tier: 2 },
  { name: 'Dehradun', state: 'Uttarakhand', tier: 2 },
] as const;

export const LOCATION_TIERS = {
  1: {
    name: 'Tier 1 (Metro)',
    description: 'Major metropolitan cities and online',
    priceMultiplier: 1,
  },
  2: {
    name: 'Tier 2',
    description: 'Clinic and home-visit cities',
    priceMultiplier: 0.7,
  },
} as const;
