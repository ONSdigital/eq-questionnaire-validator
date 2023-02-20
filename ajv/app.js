import Ajv2020 from "ajv/dist/2020.js";
import fs from "fs";
import glob from "glob";
import express from "express";
import Debug from "debug";

const debug = Debug("ajv-schema-validator");

const app = express();

const ajValidator = new Ajv2020({
  allErrors: false,
  strict: true,
  strictSchema: false, // to avoid key errors as a part of strict being true. https://ajv.js.org/options.html#strictschema
});

app.use(
  express.json({
    limit: "2Mb",
  })
);

app.listen(5002, () => {
  debug("Server running on port 5002");
});

app.get("/status", (req, res, next) => {
  return res.sendStatus(200);
});

glob("schemas/**/*.json", (er, schemas) => {
  schemas.forEach((currentSchema) => {
    const data = fs.readFileSync(currentSchema); // eslint-disable-line security/detect-non-literal-fs-filename
    ajValidator.addSchema(JSON.parse(data));
  });
  const baseSchema = fs.readFileSync("schemas/questionnaire_v1.json");
  const validate = ajValidator.compile(baseSchema);

  app.post("/validate", (req, res, next) => {
    const valid = validate(req.body);
    debug("Validating questionnaire: " + req.body.title);
    if (!valid) {
      return res.json({
        success: false,
        errors: validate.errors.sort((errorA, errorB) => {
          return errorA.dataPath.length - errorB.dataPath.length;
        }),
      });
    }
    return res.json({});
  });
});
