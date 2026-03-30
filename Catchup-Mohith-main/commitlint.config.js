// commitlint.config.js
// Enforces conventional commit format on every commit message
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'chore', 'test', 'docs', 'refactor',
       'style', 'ci', 'perf']
    ],
    'subject-max-length': [2, 'always', 100],
    'body-max-line-length': [0, 'always']
  }
}
