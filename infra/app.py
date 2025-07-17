#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.data_stack import DataStack
from stacks.api_stack  import ApiStack

app   = cdk.App()
data  = DataStack(app,  "DataStack")
api   = ApiStack(app,   "ApiStack", data.out_props)

app.synth()
