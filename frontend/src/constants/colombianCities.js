export const COLOMBIA_LOCATIONS = {
  Amazonas: ["Leticia"],
  Antioquia: [
    "Apartadó",
    "Bello",
    "Envigado",
    "Itagüí",
    "La Ceja",
    "Medellín",
    "Rionegro",
    "Sabaneta",
  ],
  Arauca: ["Arauca"],
  Atlántico: ["Barranquilla", "Puerto Colombia", "Soledad"],
  "Bogotá D.C.": ["Bogotá"],
  Bolívar: ["Cartagena", "Magangué"],
  Boyacá: ["Duitama", "Sogamoso", "Tunja"],
  Caldas: ["Manizales"],
  Caquetá: ["Florencia"],
  Casanare: ["Yopal"],
  Cauca: ["Popayán"],
  Cesar: ["Aguachica", "Valledupar"],
  Chocó: ["Quibdó"],
  Córdoba: ["Montería"],
  Cundinamarca: [
    "Cajicá",
    "Chía",
    "Facatativá",
    "Fusagasugá",
    "Girardot",
    "Madrid",
    "Mosquera",
    "Soacha",
    "Zipaquirá",
  ],
  Guainía: ["Inírida"],
  Guaviare: ["San José del Guaviare"],
  Huila: ["Neiva"],
  "La Guajira": ["Maicao", "Riohacha"],
  Magdalena: ["Ciénaga", "Santa Marta"],
  Meta: ["Villavicencio"],
  Nariño: ["Ipiales", "Pasto"],
  "Norte de Santander": ["Cúcuta", "Pamplona"],
  Putumayo: ["Puerto Asís"],
  Quindío: ["Armenia"],
  Risaralda: ["Dosquebradas", "Pereira"],
  "San Andrés y Providencia": ["San Andrés"],
  Santander: [
    "Barrancabermeja",
    "Bucaramanga",
    "Floridablanca",
    "Girón",
    "Piedecuesta",
  ],
  Sucre: ["Sincelejo"],
  Tolima: ["Ibagué"],
  Vaupés: ["Mitú"],
  "Valle del Cauca": [
    "Buga",
    "Buenaventura",
    "Cali",
    "Cartago",
    "Jamundí",
    "Palmira",
    "Tuluá",
  ],
  Vichada: ["Puerto Carreño"],
};

export const COLOMBIAN_DEPARTMENTS = Object.keys(COLOMBIA_LOCATIONS).sort(
  (a, b) => a.localeCompare(b, "es"),
);

export function departmentForCity(city) {
  return (
    COLOMBIAN_DEPARTMENTS.find((department) =>
      COLOMBIA_LOCATIONS[department].includes(city),
    ) || ""
  );
}
