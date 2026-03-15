#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.infra_stack import McpForgeStack


app = cdk.App()
McpForgeStack(app, "McpForgeStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
