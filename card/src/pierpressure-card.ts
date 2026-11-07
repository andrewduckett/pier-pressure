import { LitElement } from "lit";

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

export class PierPressureCard extends LitElement {}

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
