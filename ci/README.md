`fly -t main login -c CONCOURSE_URL`

Add EQ Schema Validator Pipeline

`fly -t main set-pipeline -p eq-schema-validator -c concourse.yml  --load-vars-from secrets.yml`