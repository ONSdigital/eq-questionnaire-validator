// Import the dependencies for testing
import chai from "chai";
import chaiHttp from "chai-http";
import app from "../app.js";
import fs from "fs";
// Configure chai
// eslint-disable-next-line import/no-named-as-default-member
chai.use(chaiHttp);
// eslint-disable-next-line import/no-named-as-default-member
chai.should();
describe("AJV api status", () => {
  describe("GET /status", () => {
    it("ajv should be live", (done) => {
      chai
        .request(app)
        .get("/status")
        .end((err, res) => {
          if (err) {
            throw new Error("Unable to execute test case");
          }
          res.should.have.status(200);
          done();
        });
    });
  });
});
// jscpd:ignore-start
describe("AJV schema Validator", () => {
  describe("POST /validate", () => {
    it("test_invalid_block_type", (done) => {
      const data = fs.readFileSync("ajv/tests/schemas/invalid/test_invalid_block_type.json");
      chai
        .request(app)
        .post("/validate")
        .set("content-type", "application/json")
        .send(JSON.parse(data))
        .end((err, res) => {
          isError(err);
          res.should.have.status(200);
          const failure = res.body.errors.pop();
          res.body.should.have.property("success", false);
          failure.should.have.property("keyword", "const");
          failure.should.have.property("message", "must be equal to constant");
          done();
        });
    });
    it("test_valid_question_description", (done) => {
      const data = fs.readFileSync("ajv/tests/schemas/valid/test_question_description.json");
      chai
        .request(app)
        .post("/validate")
        .set("content-type", "application/json")
        .send(JSON.parse(data))
        .end((err, res) => {
          isError(err);
          res.should.have.status(200);
          res.body.should.not.have.property("success", false);
          done();
        });
    });
  });
});
// jscpd:ignore-end
function isError(err) {
  if (err) {
    throw new Error("Unable to execute test case");
  }
}
