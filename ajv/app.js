const Ajv = require('ajv')
const fs = require('fs')
const glob = require('glob')
const express = require('express')
const app = express()
const debug = require('debug')('validator')

const ajv = new Ajv({
  meta: false,
  extendRefs: true,
  unknownFormats: 'ignore',
  allErrors: false,
  schemaId: 'auto'
})
ajv.addMetaSchema(require('ajv/lib/refs/json-schema-draft-07.json'))

app.use(express.json({
  limit: '2Mb'
}))

app.listen(5001, () => {
  debug('Server running on port 5001')
})

app.get('/status', (req, res, next) => {
  return res.sendStatus(200)
})

glob('../schemas/**/*.json', function(er, schemas) {
  schemas.forEach((currentSchema) => {
    const data = fs.readFileSync(currentSchema) // eslint-disable-line security/detect-non-literal-fs-filename
    ajv.addSchema(JSON.parse(data))
  })

  const validate = ajv.compile(require('../schemas/questionnaire_v1.json'))

  app.post('/validate', (req, res, next) => {
    const valid = validate(req.body)
    debug('Validating questionnaire: ' + req.body.title)
    if (!valid) {
      return res.json({
        success: false,
        errors: validate.errors.sort((errorA, errorB) => {
          return errorA.dataPath.length - errorB.dataPath.length
        })
      })
    }
    return res.json({})
  })
})
