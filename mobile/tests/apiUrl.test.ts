import assert from "node:assert/strict";
import { test } from "node:test";

import { apiBaseUrl } from "../services/apiUrl.ts";

test("in development the API is on the same Mac as Expo, port 8000", () => {
  assert.equal(apiBaseUrl("192.168.1.20:8081"), "http://192.168.1.20:8000");
  assert.equal(apiBaseUrl("192.168.1.20:8081/--/"), "http://192.168.1.20:8000");
});

test("without Expo information it uses this computer", () => {
  assert.equal(apiBaseUrl(undefined), "http://localhost:8000");
  assert.equal(apiBaseUrl(""), "http://localhost:8000");
});

test("an explicit address wins (the deployed API, later)", () => {
  assert.equal(apiBaseUrl("192.168.1.20:8081", "https://api.cookinerapp.com/"), "https://api.cookinerapp.com");
});
