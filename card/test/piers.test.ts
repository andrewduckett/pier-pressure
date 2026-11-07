import { describe, expect, it } from "vitest";
import { listPiers } from "../src/entity";
import { verdictEntity } from "./harness";

describe("listPiers", () => {
  it("lists a pier by its pier attribute when that attribute finds the sensor", () => {
    const states = {
      "sensor.pierpressure_back_yard_verdict": verdictEntity("GO", { pier: "Back-Yard" }),
    };

    expect(listPiers(states)).toEqual([{ value: "Back-Yard", label: "Back-Yard" }]);
  });

  it("sets the slug for a pier id the slug rule cannot match", () => {
    const states = {
      "sensor.pierpressure_dong_jing_verdict": verdictEntity("GO", { pier: "東京" }),
    };

    expect(listPiers(states)).toEqual([{ value: "dong_jing", label: "東京" }]);
  });

  it("lists a pier before its first verdict by its slug", () => {
    const states = { "sensor.pierpressure_backyard_verdict": verdictEntity("unknown") };

    expect(listPiers(states)).toEqual([{ value: "backyard", label: "backyard" }]);
  });

  it("takes the slug from the entity id when the pier attribute is not text", () => {
    const states = { "sensor.pierpressure_backyard_verdict": verdictEntity("GO", { pier: 7 }) };

    expect(listPiers(states)).toEqual([{ value: "backyard", label: "backyard" }]);
  });

  it.each([
    ["another PierPressure sensor", "sensor.pierpressure_backyard_score"],
    ["another integration's verdict", "sensor.weather_verdict"],
    ["a verdict with no slug", "sensor.pierpressure__verdict"],
  ])("leaves out %s", (_label, entityId) => {
    expect(listPiers({ [entityId]: verdictEntity("GO") })).toEqual([]);
  });

  it("leaves out an entity id with no entity", () => {
    expect(listPiers({ "sensor.pierpressure_backyard_verdict": undefined })).toEqual([]);
  });

  it("lists the piers in alphabetical order", () => {
    const states = {
      "sensor.pierpressure_frontyard_verdict": verdictEntity("GO", { pier: "frontyard" }),
      "sensor.pierpressure_back_yard_verdict": verdictEntity("GO", { pier: "Back-Yard" }),
    };

    expect(listPiers(states).map((pier) => pier.label)).toEqual(["Back-Yard", "frontyard"]);
  });
});
