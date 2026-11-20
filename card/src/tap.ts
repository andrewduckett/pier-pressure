// What a tap on the card shows: the tapped item's hover text in a box.

export interface Size {
  width: number;
  height: number;
}

export interface Rect extends Size {
  left: number;
  top: number;
}

// How far, in px, the box keeps from the card's edges, and from its item.
const EDGE = 8;
const GAP = 4;

// In px from the card's top left corner. The box centres on the part of the item
// inside the card, so a bar the axis cuts off centres on what shows.
export function placeTip(item: Rect, card: Rect, box: Size): { left: number; top: number } {
  const from = Math.max(item.left, card.left);
  const to = Math.min(item.left + item.width, card.left + card.width);
  const centre = (from + to) / 2 - card.left;
  const left = Math.max(EDGE, Math.min(centre - box.width / 2, card.width - EDGE - box.width));
  const above = item.top - card.top - GAP - box.height;
  const top = above < EDGE ? item.top - card.top + item.height + GAP : above;
  return { left, top };
}
