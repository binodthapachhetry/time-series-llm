from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_apigatewayv2_alpha as apigw,
    aws_apigatewayv2_integrations_alpha as integrations,
    aws_iam as iam, 
    CfnOutput,
)
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct

from .data_stack import DataProps


class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, data: DataProps, **kw) -> None:
        super().__init__(scope, id, **kw)

        # locate repo root: this file -> stacks -> infra -> (repo root)
        repo_root = Path(__file__).resolve().parents[2]
        src_path = repo_root / "src"

        if not src_path.exists():
            raise FileNotFoundError(f"Lambda source dir not found: {src_path}")

        fn = PythonFunction(
            self,
            "TimeseriesAgent",
            entry=str(src_path),  # directory containing handler.py
            index="handler.py",   # file inside entry dir
            handler="handler",    # function name in handler.py
            runtime=_lambda.Runtime.PYTHON_3_11,
            memory_size=512,
            timeout=Duration.seconds(10),
            environment={
                "DB_NAME": data.db_name,
                "TABLE": data.tbl_name,
                "MODEL_ID": data.model_id,
            },
        )
        
        # Inline IAM permissions required by Lambda
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "timestream:DescribeEndpoints",
                    "timestream:Select",
                    "timestream:SelectValues",
                ],
                resources=["*"],  # tighten later
            )
        )
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],  # or specific model ARN
            )
        )

        api = apigw.HttpApi(
            self,
            "PublicAPI",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.POST],
            ),
        )

        api.add_routes(
            path="/query",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration("Hook", fn),
        )

        self.api_url = api.api_endpoint
        CfnOutput(self, "ApiUrl", value=api.api_endpoint)

