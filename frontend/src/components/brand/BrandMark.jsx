export function BrandMark({ className = "" }) {
  return <svg className={`brand-symbol ${className}`} viewBox="0 0 128 128" fill="none" aria-hidden="true" focusable="false">
    <circle cx="39" cy="24" r="12" fill="var(--brand-candidate)" />
    <circle cx="89" cy="24" r="12" fill="var(--brand-company)" />
    <path d="M59 52C47 41 28 43 18 57C3 78 10 104 32 112C44 116 57 111 66 101L52 88C46 95 39 97 33 93C24 87 26 76 34 71C40 67 46 70 50 74L64 61L59 52Z" fill="var(--brand-candidate)" />
    <path d="M59 52C47 41 28 43 18 57C3 78 10 104 32 112C44 116 57 111 66 101L52 88C46 95 39 97 33 93C24 87 26 76 34 71C40 67 46 70 50 74L64 61L59 52Z" transform="translate(128 0) scale(-1 1)" fill="var(--brand-company)" />
    <circle cx="64" cy="80" r="10" fill="var(--brand-admin)" />
  </svg>;
}
