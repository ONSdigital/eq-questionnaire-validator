const gulp = require("gulp");
const beautify = require("gulp-jsbeautifier");
const diff = require("gulp-diff");
const gutil = require("gulp-util");

const beautifySettings = {
    indent_size: 2, //eslint-disable-line camelcase
    end_with_newline: true //eslint-disable-line camelcase

};

const formatPaths = [
  "./schemas/**",
  "./tests/schemas/**"
];

gulp.task("format", () =>
  gulp.src(formatPaths, {base: "./"})
    .pipe(beautify(beautifySettings))
    .pipe(gulp.dest("."))
);

gulp.task("lint", () =>
  gulp.src(formatPaths)
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
