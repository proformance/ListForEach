#!/bin/bash

if [ -z "${ARTIFACT_BUCKET}" ]; then
    echo "This deployment script needs an S3 bucket to store CloudFormation artifacts."
    echo "You can also set this by doing: export ARTIFACT_BUCKET=my-bucket-name"
    echo
    read -p "S3 bucket to store artifacts: " ARTIFACT_BUCKET
fi

MACRO_NAME=$(basename $(pwd))

aws cloudformation package \
    --template-file macro_template.yaml \
    --s3-bucket ${ARTIFACT_BUCKET} \
    --output-template-file macro_packaged.yaml

aws cloudformation deploy \
    --stack-name ${MACRO_NAME}-macro \
    --template-file macro_packaged.yaml \
    --capabilities CAPABILITY_IAM
