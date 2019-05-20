const gulp = require("gulp");
const beautify = require("gulp-jsbeautifier");
const diff = require("gulp-diff");
const gutil = require("gulp-util");

const beautifySettings = {
    indent_size: 2, //eslint-disable-line camelcase
    end_with_newline: true //eslint-disable-line camelcase

};

const formatPath = "./tests/schemas/*/**.json";

gulp.task("format", () =>
  gulp.src([formatPath])
    .pipe(beautify(beautifySettings))
    .pipe(gulp.dest("./tests/schemas/"))
);

gulp.task("lint", () =>
  gulp.src([formatPath])
    .pipe(beautify(beautifySettings))
    .pipe(diff())
    .pipe(
      diff.reporter({
        quiet: false,
        fail: true
      })
    )
    .on("error", (err) => {
    gutil.log("Linting failed try running `gulp format`");
    throw err;
  })
);
