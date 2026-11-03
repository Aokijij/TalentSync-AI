import { CarFront, Truck } from "lucide-react";

export const categoryLabels = { A1: "Motocicleta hasta 125 cc", A2: "Motocicleta de más de 125 cc", B1: "Automóvil · particular", B2: "Camión o bus · particular", B3: "Articulado · particular", C1: "Automóvil · servicio público", C2: "Camión o bus · servicio público", C3: "Articulado · servicio público" };

export function DrivingCategoryIcon({ category = "", size = 20 }) {
  if (category.startsWith("A")) return <svg data-vehicle="motorcycle" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="5" cy="17" r="3.5" /><circle cx="19" cy="17" r="3.5" /><path d="M5 17l5-8h4l5 8M8 12h7M4 10h5M14 6h3l2 8M10 9l4 8H5" /></svg>;
  if (category.endsWith("3")) return <svg data-vehicle="articulated" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M2 5h12v11H2zM14 9h5l3 4v4h-8M18 9v5h4" /><circle cx="6" cy="18" r="2" /><circle cx="17.5" cy="18" r="2" /></svg>;
  const Icon = category.endsWith("2") ? Truck : CarFront;
  return <Icon data-vehicle={category.endsWith("2") ? "heavy" : "car"} size={size} aria-hidden="true" />;
}
