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

export interface PierChoice {
  value: string;
  label: string;
}

const VERDICT_ID = /^sensor\.pierpressure_(.+)_verdict$/;

// The pier attribute names the pier, but only a value that slugs back to the
// sensor's own id finds it: a pier id in another alphabet, or a sensor before
// its first verdict, is set by the slug in its id instead.
export function listPiers(
  states: Record<string, { attributes: Record<string, unknown> } | undefined>,
): PierChoice[] {
  const piers: PierChoice[] = [];
  for (const [entityId, entity] of Object.entries(states)) {
    const slug = VERDICT_ID.exec(entityId)?.[1];
    if (slug === undefined || entity === undefined) continue;
    const pier = entity.attributes["pier"];
    const named = typeof pier === "string" && pier !== "" ? pier : undefined;
    piers.push({
      value: named !== undefined && pierSlug(named) === slug ? named : slug,
      label: named ?? slug,
    });
  }
  return piers.sort((a, b) => a.label.localeCompare(b.label) || a.value.localeCompare(b.value));
}
