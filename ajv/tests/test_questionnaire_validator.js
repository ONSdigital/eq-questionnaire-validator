// Import the dependencies for testing
import chai from "chai";
import chaiHttp from "chai-http";
import app from "../app";
import fs from "fs";
// Configure chai
chai.use(chaiHttp);
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
describe("AJV schema Validator", () => {
  describe("POST /validate", () => {
    it("test_invalid_question_description", (done) => {
      const data = fs.readFileSync(
        "ajv/tests/schemas/invalid/test_invalid_question_description.json"
      );
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
          failure.should.have.property(
            "message",
            "must be equal to one of the allowed values"
          );
          done();
        });
    });
    it("test_valid_question_description", (done) => {
      const data = fs.readFileSync(
        "ajv/tests/schemas/valid/test_question_description.json"
      );
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
function isError(err) {
  if (err) {
    throw new Error("Unable to execute test case");
  }
}
