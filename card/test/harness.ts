import type { HassEntity, HomeAssistant, PierPressureCard } from "../src/pierpressure-card";

export const VERDICT = "sensor.pierpressure_backyard_verdict";

export function verdictEntity(state: string, attributes: Record<string, unknown> = {}): HassEntity {
  return { state, attributes };
}

export async function mountCard(
  states?: Record<string, HassEntity>,
  pier = "backyard",
  timeZone = "UTC",
): Promise<PierPressureCard> {
  const card = document.createElement("pierpressure-card") as PierPressureCard;
  card.setConfig({ type: "custom:pierpressure-card", pier });
  document.body.append(card);
  if (states !== undefined) {
    const hass: HomeAssistant = { states, config: { time_zone: timeZone } };
    card.hass = hass;
  }
  await card.updateComplete;
  return card;
}

export function field(card: PierPressureCard, name: string): string | undefined {
  return card.shadowRoot?.querySelector(`[data-field="${name}"]`)?.textContent?.trim();
}

export function cardText(card: PierPressureCard): string {
  return card.shadowRoot?.textContent?.replace(/\s+/g, " ").trim() ?? "";
}

export const CLOUD_COVER = "sensor.pierpressure_backyard_cloud_cover";
export const CLOUD_LOW = "sensor.pierpressure_backyard_cloud_low";
export const CLOUD_MID = "sensor.pierpressure_backyard_cloud_mid";
export const CLOUD_HIGH = "sensor.pierpressure_backyard_cloud_high";
export const SUN_ALTITUDE = "sensor.pierpressure_backyard_sun_altitude";
export const MOON_ALTITUDE = "sensor.pierpressure_backyard_moon_altitude";
export const WIND_GUST = "sensor.pierpressure_backyard_wind_gust";
export const SEEING = "sensor.pierpressure_backyard_seeing";
export const TRANSPARENCY = "sensor.pierpressure_backyard_transparency";
export const TEMPERATURE = "sensor.pierpressure_backyard_temperature";
export const DEW_POINT = "sensor.pierpressure_backyard_dew_point";
export const HUMIDITY = "sensor.pierpressure_backyard_humidity";
export const WIND_SPEED = "sensor.pierpressure_backyard_wind_speed";
export const WIND_DIRECTION = "sensor.pierpressure_backyard_wind_direction";
export const PRECIPITATION_PROBABILITY = "sensor.pierpressure_backyard_precipitation_probability";

// Any timeline sensor as PierPressure publishes it: the current hour's value as its
// state, and every hour in `forecast`.
export function forecastEntity(points: Array<[string, unknown]>, state = "40"): HassEntity {
  return {
    state,
    attributes: { forecast: points.map(([datetime, value]) => ({ datetime, value })) },
  };
}

export function cells(card: PierPressureCard, row: string): HTMLElement[] {
  return [
    ...(card.shadowRoot?.querySelectorAll<HTMLElement>(`.strip [data-row="${row}"] .cell`) ?? []),
  ];
}

export function moonLane(card: PierPressureCard): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>('.strip [data-lane="moon_up"]') ?? null;
}

export function bars(card: PierPressureCard): HTMLElement[] {
  return [...(moonLane(card)?.querySelectorAll<HTMLElement>(".bar") ?? [])];
}

export function line(card: PierPressureCard, kind: string): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>(`.strip [data-line="${kind}"]`) ?? null;
}

export function mark(card: PierPressureCard, kind: string): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>(`.strip [data-mark="${kind}"]`) ?? null;
}
