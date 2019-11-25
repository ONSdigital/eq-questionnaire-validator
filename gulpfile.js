const gulp = require('gulp')
const prettier = require('gulp-prettier')
const diff = require('gulp-diff')
const gutil = require('gulp-util')

const formatPaths = ['./schemas/**', './tests/schemas/**']

gulp.task('format', () =>
  gulp
    .src(formatPaths, {
      base: './'
    })
    .pipe(prettier())
    .pipe(gulp.dest('.'))
)

gulp.task('lint', () =>
  gulp
    .src(formatPaths)
    .pipe(prettier())
    .pipe(diff())
    .pipe(
      diff.reporter({
        quiet: false,
        fail: true
      })
    )
    .on('error', (err) => {
      gutil.log('Linting failed try running `gulp format`')
      throw err
    })
)
