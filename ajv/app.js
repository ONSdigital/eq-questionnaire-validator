import Ajv2020 from "ajv/dist/2020.js";
import fs from "fs";
import { globSync } from "glob";
import express from "express";
import Debug from "debug";

const debug = Debug("ajv-schema-validator");
const app = express();
const AJV_VALIDATOR_PORT = process.env.AJV_VALIDATOR_PORT || 5002;

app.use(
  express.json({
    limit: "2Mb",
  })
);

app.listen(AJV_VALIDATOR_PORT, () => {
  debug(`Server running on port  ${AJV_VALIDATOR_PORT}`);
});

const ajValidator = new Ajv2020({
  allErrors: false,
  strict: true,
  strictRequired: false, // this has been included to avoid required implementation inside anyOf/oneOf
  strictTypes: false, // this has been included to avoid missing types as strict mode is true
  strictSchema: false, // this has been included to avoid unknown keyword errors ad strict mode is true
  strictTuples: false, // this has been included due to https://github.com/ajv-validator/ajv/issues/1417
});

const schemas = globSync("schemas/**/*.json");
schemas.forEach((currentSchema) => {
  if (!(currentSchema.valueOf() === "schemas/questionnaire_v1.json")) {
    const data = fs.readFileSync(currentSchema);
    debug("Adding schema: " + currentSchema);
    ajValidator.addSchema(JSON.parse(data)).compile(true);
  }
});

const baseSchema = fs.readFileSync("schemas/questionnaire_v1.json");
const validate = ajValidator.compile(JSON.parse(baseSchema));

app.get("/status", (req, res, next) => {
  return res.sendStatus(200);
});

app.post("/validate", (req, res, next) => {
  debug("Validating questionnaire: " + req.body.title);
  const valid = validate(req.body);
  if (!valid) {
    return res.json({
      success: false,
      errors: validate.errors.sort((errorA, errorB) => {
        return errorA.instancePath.length - errorB.instancePath.length;
      }),
    });
  }
  return res.json({});
});

// Export our app for testing purposes
export default app;
