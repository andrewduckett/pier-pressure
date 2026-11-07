// Home Assistant names the Verdict sensor from its device, "PierPressure <pier>",
// and its entity name, "Verdict". This follows Home Assistant's slug rule for
// ASCII and accented Latin pier ids; it does not transliterate other scripts.
export function pierSlug(pier: string): string {
  return pier
    .toLowerCase()
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

export function verdictEntityId(pier: string): string {
  return `sensor.pierpressure_${pierSlug(pier)}_verdict`;
}
