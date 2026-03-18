import request from "supertest";
import app from "../app.js";
import fs from "fs";
import { expect } from "@jest/globals";

describe("AJV api status", () => {
  describe("GET /status", () => {
    it("ajv should be live", async () => {
      const res = await request(app).get("/status");
      expect(res.status).toBe(200);
    });
  });
});

describe("AJV schema Validator", () => {
  describe("POST /validate", () => {
    it("test_invalid_block_type", async () => {
      const data = fs.readFileSync("ajv/tests/schemas/invalid/test_invalid_block_type.json");
      const res = await request(app).post("/validate").set("content-type", "application/json").send(JSON.parse(data));
      expect(res.status).toBe(200);
      const failure = res.body.errors.pop();
      expect(res.body.success).toBe(false);
      expect(failure.keyword).toBe("const");
      expect(failure.message).toBe("must be equal to constant");
    });

    it("test_valid_question_description", async () => {
      const data = fs.readFileSync("ajv/tests/schemas/valid/test_question_description.json");
      const res = await request(app).post("/validate").set("content-type", "application/json").send(JSON.parse(data));
      expect(res.status).toBe(200);
      expect(res.body.success).not.toBe(false);
    });
  });
});
