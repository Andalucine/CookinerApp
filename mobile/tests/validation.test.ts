import assert from "node:assert/strict";
import { test } from "node:test";

import { checkCode, checkEmail, checkPassword, checkRequired } from "../services/validation.ts";

test("email", () => {
  assert.equal(checkEmail(""), "error.required");
  assert.equal(checkEmail("beatriz"), "error.email");
  assert.equal(checkEmail(" beatriz@correo.es "), null);
});

test("password: at least 8 characters, like the API", () => {
  assert.equal(checkPassword(""), "error.required");
  assert.equal(checkPassword("1234567"), "error.password");
  assert.equal(checkPassword("12345678"), null);
});

test("required and 6-digit code", () => {
  assert.equal(checkRequired("  "), "error.required");
  assert.equal(checkRequired("Ana"), null);
  assert.equal(checkCode("12345"), "error.code");
  assert.equal(checkCode("12a456"), "error.code");
  assert.equal(checkCode("123456"), null);
});
