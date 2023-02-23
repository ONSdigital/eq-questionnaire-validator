// Import the dependencies for testing
import chai from "chai";
import chaiHttp from "chai-http";
import app from "../app";
// Configure chai
chai.use(chaiHttp);
chai.should();
describe("AJV api status", () => {
  describe("POST /", () => {
    it("should get ok status", (done) => {
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
