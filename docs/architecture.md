graph TD
    User -->|POST /query| APIGW
    APIGateway --> Lambda
    Lambda -->|SELECT*| Timestream
    Lambda -->|InvokeModel| Bedrock
    Bedrock --> Lambda
    Lambda -->|JSON answer| APIGW
    APIGW --> User
