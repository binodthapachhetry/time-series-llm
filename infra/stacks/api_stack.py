from aws_cdk import (
    Stack, Duration,
    aws_lambda_python_alpha as lambda_py,
    aws_apigatewayv2_alpha as apigw,
    aws_apigatewayv2_integrations_alpha as integrations,
)
from constructs import Construct
from .data_stack import DataProps

class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, data: DataProps, **kw):
        super().__init__(scope, id, **kw)

        fn = lambda_py.PythonFunction(
            self, "TimeseriesAgent",
            entry       ="src",
            index       ="handler.py",
            handler     ="handler",
            runtime     =lambda_py.PythonRuntime.PYTHON_3_11,
            memory_size =512,
            timeout     =Duration.seconds(10),
            environment ={
                "DB_NAME":   data.db_name,
                "TABLE":     data.tbl_name,
                "MODEL_ID":  data.model_id},
                deps_lock_file_path="src/requirements.txt",
            )
        fn.role.add_managed_policy(data.lambda_policy)

        api = apigw.HttpApi(self, "PublicAPI",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.POST]))

        api.add_routes(
            path="/query",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration("Hook", fn)
        )

        self.api_url = api.api_endpoint
