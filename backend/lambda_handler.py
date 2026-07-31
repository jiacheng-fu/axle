"""AWS Lambda entrypoint.

Mangum translates API Gateway's event/context into the ASGI calls FastAPI
expects, so the same ``app`` serves both ``uvicorn main:app`` locally and Lambda
in production. There is no separate Lambda code path to keep in sync.

    handler = lambda_handler.handler      (set as the Lambda Handler)

Deployed via template.yaml. Locally nothing imports this module, so Mangum stays
an optional dependency for anyone running the API with uvicorn.
"""

from mangum import Mangum

from main import app

# lifespan="off": FastAPI startup/shutdown events assume a long-lived process.
# Lambda freezes and thaws the container between invocations, so running them per
# request is wasted work at best and misleading at worst.
# api_gateway_base_path strips the stage from the path before FastAPI routes it.
# The API is deployed to the "prod" stage, so API Gateway hands Mangum "/prod/dealers";
# without this FastAPI sees a path it has no route for and returns 404 for everything.
handler = Mangum(app, lifespan="off", api_gateway_base_path="/prod")
