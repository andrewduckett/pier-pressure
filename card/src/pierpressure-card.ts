import { LitElement } from "lit";
import { pierSlug } from "./entity";

declare const __CARD_VERSION__: string;

export const CARD_VERSION: string = __CARD_VERSION__;

const CARD_TYPE = "pierpressure-card";

interface CustomCardEntry {
  type: string;
  name: string;
  description?: string;
}

declare global {
  interface Window {
    customCards?: CustomCardEntry[];
  }
}

export interface CardConfig {
  type: string;
  pier: string;
}

export class PierPressureCard extends LitElement {
  static override properties = {
    config: { state: true },
  };

  declare config?: CardConfig;

  // Home Assistant shows a thrown error in place of the card.
  setConfig(config: Record<string, unknown>): void {
    const pier = config["pier"];
    if (typeof pier !== "string" || pierSlug(pier) === "") {
      throw new Error("pier is required");
    }
    this.config = { type: String(config["type"]), pier };
  }
}

// HACS can load the file again when it updates the card in place; defining
// the element twice throws, and a second entry would show twice in the picker.
if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, PierPressureCard);
}
window.customCards ??= [];
if (!window.customCards.some((card) => card.type === CARD_TYPE)) {
  window.customCards.push({
    type: CARD_TYPE,
    name: "PierPressure",
    description: "Tonight's verdict, score and confidence for one pier.",
  });
}
console.info(`PIERPRESSURE-CARD ${CARD_VERSION}`);
