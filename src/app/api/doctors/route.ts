/**
 * H2H Healthcare - Doctors API
 * Fetch doctors from database (fully dynamic)
 */

import { createAdminClient } from '@/lib/supabase/server';
import { resolveDoctorAvatarSrc } from '@/constants/doctor-avatars';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const supabase = createAdminClient();
    const searchParams = request.nextUrl.searchParams;
    
    const locationId = searchParams.get('locationId');
    const serviceId = searchParams.get('serviceId');
    const category = searchParams.get('category');
    const centerId = searchParams.get('centerId'); // Filter by specific clinic center
    const date = searchParams.get('date'); // YYYY-MM-DD format
    const mode = searchParams.get('mode'); // online, offline, both

    const ONLINE_LOCATION_IDS = new Set([
      'online',
      '33333333-3333-3333-3333-333333333333',
    ]);
    const isOnlineContext =
      mode === 'online' ||
      (!!locationId && ONLINE_LOCATION_IDS.has(locationId));

    let query = supabase
      .from('doctors')
      .select(`
        *,
        users:user_id(id, full_name, email, avatar_url, phone),
        locations:location_id(id, name, city),
        doctor_availability(*),
        doctor_services(service_id)
      `)
      .eq('is_active', true);

    // Primary location filter — skip for online / worldwide telehealth
    if (locationId && !isOnlineContext && !centerId) {
      query = query.eq('location_id', locationId);
    }

    const { data: doctors, error } = await query;

    if (error) {
      console.error('Error fetching doctors:', error);
      return NextResponse.json({
        success: false,
        error: 'Failed to fetch doctors',
        data: [],
        count: 0,
      }, { status: 500 });
    }

    // Filter by service if provided
    let filteredDoctors = doctors || [];

    if (serviceId || category) {
      let serviceIdsForFilter = new Set<string>();

      if (serviceId) {
        serviceIdsForFilter.add(serviceId);
      }

      if (category) {
        const { data: categoryServices } = await supabase
          .from('services')
          .select('id')
          .eq('category', category)
          .eq('is_active', true);
        categoryServices?.forEach((s) => serviceIdsForFilter.add(s.id));
      }

      if (serviceIdsForFilter.size > 0) {
        filteredDoctors = filteredDoctors.filter((doctor: any) =>
          doctor.doctor_services?.some((s: any) => serviceIdsForFilter.has(s.service_id))
        );
      }
    }

    // If date provided, filter by availability on that day
    if (date) {
      const dayOfWeek = new Date(date).getDay();
      filteredDoctors = filteredDoctors.filter((doctor: any) =>
        doctor.doctor_availability?.some((a: any) => 
          a.day_of_week === dayOfWeek && a.is_available
        )
      );
    }

    // Filter by mode (online/offline/both)
    if (mode) {
      filteredDoctors = filteredDoctors.filter((doctor: any) => {
        if (mode === 'online') return doctor.offers_online;
        if (mode === 'offline') return doctor.offers_clinic;
        return true;
      });
    }

    // Filter by center availability — not applicable for online telehealth
    if (centerId && !isOnlineContext) {
      filteredDoctors = filteredDoctors.filter((doctor: any) => {
        // Check if any of the doctor's availability slots include this center
        return doctor.doctor_availability?.some((a: any) => {
          // Check if the availability has center_id matching
          if (a.center_id === centerId) return true;
          // Also check slots array if it exists (new format)
          if (a.slots && Array.isArray(a.slots)) {
            return a.slots.some((slot: any) => slot.center_id === centerId);
          }
          // Fallback: If center_id is null and mode is offline/both, include the doctor
          // This handles legacy data where center_id wasn't set
          if (a.center_id === null && (a.mode === 'offline' || a.mode === 'both')) {
            return true;
          }
          return false;
        });
      });
    }

    // Transform data for frontend
    const transformedDoctors = filteredDoctors.map((doctor: any) => ({
      id: doctor.id,
      name: doctor.users?.full_name || 'Unknown',
      email: doctor.users?.email,
      avatar: resolveDoctorAvatarSrc({
        name: doctor.users?.full_name,
        email: doctor.users?.email,
        avatar: doctor.users?.avatar_url,
      }),
      phone: doctor.users?.phone,
      specializations: doctor.specializations || [],
      qualifications: doctor.qualifications || [],
      experience_years: doctor.experience_years || 0,
      bio: doctor.bio,
      rating: doctor.rating || 5.0,
      total_reviews: doctor.total_reviews || 0,
      consultation_fee: doctor.consultation_fee || 1000,
      google_meet_enabled: doctor.google_meet_enabled,
      // Consultation modes
      offers_online: doctor.offers_online ?? true,
      offers_clinic: doctor.offers_clinic ?? true,
      offers_home_visit: doctor.offers_home_visit ?? false,
      home_visit_radius_km: doctor.home_visit_radius_km ?? 10,
      location: doctor.locations,
      availability: doctor.doctor_availability || [],
      services: doctor.doctor_services?.map((ds: any) => ds.service_id) || [],
    }));

    return NextResponse.json({
      success: true,
      data: transformedDoctors,
      count: transformedDoctors.length,
      source: 'database',
    });
  } catch (error) {
    console.error('Error in doctors API:', error);
    return NextResponse.json({
      success: false,
      error: 'Internal server error',
      data: [],
      count: 0,
    }, { status: 500 });
  }
}
