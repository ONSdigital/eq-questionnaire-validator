import Ajv2020 from "ajv/dist/2020.js";
import fs from "fs";
import glob from "glob";
import express from "express";
import Debug from "debug";

const debug = Debug("ajv-schema-validator");

const app = express();

const ajValidator = new Ajv2020({
  allErrors: false,
  strict: "log",
  strictRequired: false, // this has been included to avoid required implementation inside anyOf/oneOf
  strictTypes: false, // this has been included to avoid missing types as strict mode is true
  strictSchema: false, // this has been included to avoid unknown keyword errors ad strict mode is true
  strictTuples: false, // this has been included due to https://github.com/ajv-validator/ajv/issues/1417
});

app.use(
  express.json({
    limit: "2Mb",
  })
);

app.listen(5002, () => {
  debug("Server running on port 5002");
});

// Export our app for testing purposes
export default app;

app.get("/status", (req, res, next) => {
  return res.sendStatus(200);
});

glob("schemas/**/*.json", (er, schemas) => {
  schemas.forEach((currentSchema) => {
    if (!(currentSchema.valueOf() === "schemas/questionnaire_v1.json")) {
      const data = fs.readFileSync(currentSchema); // eslint-disable-line security/detect-non-literal-fs-filename
      ajValidator.addSchema(JSON.parse(data)).compile(true);
    }
  });
  const baseSchema = fs.readFileSync("schemas/questionnaire_v1.json");
  const validate = ajValidator.compile(JSON.parse(baseSchema));

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
});
