from flask import Flask
from pydantic import BaseModel

from spectree import SecurityScheme, SecuritySchemeData, SpecTree


class Req(BaseModel):
    name: str


security_schemes = [
    SecurityScheme(
        name="PartnerID",
        data=SecuritySchemeData.model_validate(
            {"type": "apiKey", "name": "partner-id", "in": "header"}
        ),
    ),
    SecurityScheme(
        name="PartnerToken",
        data=SecuritySchemeData.model_validate(
            {"type": "apiKey", "name": "partner-access-token", "in": "header"}
        ),
    ),
    SecurityScheme(
        name="test_secure",
        data=SecuritySchemeData.model_validate(
            {
                "type": "http",
                "scheme": "bearer",
            }
        ),
    ),
    SecurityScheme(
        name="auth_oauth2",
        data=SecuritySchemeData.model_validate(
            {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": (
                            "https://accounts.google.com/o/oauth2/v2/auth"
                        ),
                        "tokenUrl": "https://sts.googleapis.com",
                        "scopes": {
                            "https://www.googleapis.com/auth/tasks.readonly": "tasks",
                        },
                    },
                },
            }
        ),
    ),
]

app = Flask(__name__)
spec = SpecTree(
    "flask",
    security_schemes=security_schemes,
    SECURITY=[
        {"test_secure": []},
        {"PartnerID": [], "PartnerToken": []},
    ],
    client_id="client_id",
)


@app.route("/ping", methods=["POST"])
@spec.validate(
    json=Req,
)
def ping():
    return "pong"


@app.route("/ping/oauth", methods=["POST"])
@spec.validate(
    json=Req,
    security=[{"auth_oauth2": ["read"]}],
)
def oauth_only():
    return "pong"


@app.route("/")
def index():
    return "hello"


if __name__ == "__main__":
    spec.register(app)
    app.run(port=8000)
