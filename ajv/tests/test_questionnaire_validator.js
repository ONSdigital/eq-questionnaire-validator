// Import the dependencies for testing
import chai from "chai";
import chaiHttp from "chai-http";
import app from "../app";
import fs from "fs";
// Configure chai
chai.use(chaiHttp);
chai.should();
const path = require("path");
describe("AJV schema Validator", () => {
  describe("GET /validate", () => {
    it("test_invalid_question_description", (done) => {
      const data = fs.readFileSync(
        path.join(
          __dirname,
          "schemas/invalid/test_invalid_question_description.json"
        )
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
          failure.should.have.property("keyword", "enum");
          failure.should.have.property(
            "message",
            "must be equal to one of the allowed values"
          );
          done();
        });
    });
    it("test_valid_question_description", (done) => {
      const data = fs.readFileSync(
        path.join(__dirname, "schemas/valid/test_question_description.json")
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
    it("test_valid_placeholder", (done) => {
      const data = fs.readFileSync(
        path.join(__dirname, "schemas/valid/test_placeholder_full.json")
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
    it("test_invalid_placeholder", (done) => {
      const data = fs.readFileSync(
        path.join(
          __dirname,
          "schemas/invalid/test_invalid_placeholder_full.json"
        )
      );
      chai
        .request(app)
        .post("/validate")
        .set("content-type", "application/json")
        .send(JSON.parse(data))
        .end((err, res) => {
          isError(err);
          res.should.have.status(200);
          res.body.should.have.property("success", false);
          const failure = res.body.errors.pop();
          failure.should.have.property("keyword", "const");
          failure.should.have.property("message", "must be equal to constant");
          done();
        });
    });
    it("test_valid_new_routing_and", (done) => {
      const data = fs.readFileSync(
        path.join(__dirname, "schemas/valid/test_new_routing_and.json")
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
    it("test_invalid_new_routing_and", (done) => {
      const data = fs.readFileSync(
        path.join(
          __dirname,
          "schemas/invalid/test_invalid_new_routing_and.json"
        )
      );
      chai
        .request(app)
        .post("/validate")
        .set("content-type", "application/json")
        .send(JSON.parse(data))
        .end((err, res) => {
          isError(err);
          res.should.have.status(200);
          res.body.should.have.property("success", false);
          const failure = res.body.errors.pop();
          failure.should.have.property("keyword", "oneOf");
          failure.should.have.property(
            "message",
            "must match exactly one schema in oneOf"
          );
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
