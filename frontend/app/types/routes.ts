// types/route.ts
export type Trip = {
  id_trip: number;
  name: string;
  origin: string;
  destination: string;
  departure_time: string | null;
  arrival_time: string | null;
  duration: number;
  distance: number;
  emission: string;
  id_agency: number;
  agency_name?: string;
};

export type Stop = {
  stop_sequence: number;
  station_name: string;
  city: string | null;
  arrival_time: string | null;
  departure_time: string | null;
  latitude: number;
  longitude: number;
};

export type Agency = {
  id_agency: number;
  code: string;
  name: string;
};

export type TripDetail = {
  trip: Trip;
  agency: Agency;
  is_night_train: boolean;
  stops: Stop[];
};

export type ApiStatsResponse = {
  nb_total_trips: number;
  nb_day_trips: number;
  nb_night_trips: number;
  nb_operators: number;
  trips_by_operator: Record<string, number>;
};

export type OperatorStat = {
  operateur: string;
  total: number;
};

export type StatsData = {
  total: number;
  jour: number;
  nuit: number;
  nbOperateurs: number;
  parOperateur: OperatorStat[];
};
