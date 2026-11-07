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

// Every PierPressure sensor of a pier is named from the same device, so only
// the entity's key differs.
export function pierEntityId(pier: string, key: string): string {
  return `sensor.pierpressure_${pierSlug(pier)}_${key}`;
}

export function verdictEntityId(pier: string): string {
  return pierEntityId(pier, "verdict");
}
