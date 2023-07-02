import re
from enum import Enum
from typing import Any, Dict, Optional, Sequence

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import Url, core_schema

# OpenAPI names validation regexp
OpenAPI_NAME_RE = re.compile(r"^[A-Za-z0-9-._]+")


class ExternalDocs(BaseModel):
    description: str = ""
    url: str


class Tag(BaseModel):
    """OpenAPI tag object"""

    name: str
    description: str = ""
    externalDocs: Optional[ExternalDocs] = None

    def __str__(self):
        return self.name


class ValidationErrorElement(BaseModel):
    """Model of a validation error response element."""

    ctx: Optional[Dict[str, Any]] = Field(
        None,
        title="Error context",
    )
    input: Any = Field(..., title="Input provided for validation")
    loc: Sequence[str] = Field(
        ...,
        title="Error location",
    )
    msg: str = Field(
        ...,
        title="Error message",
    )
    type: str = Field(  # noqa: WPS125
        ...,
        title="Error type",
    )
    url: Url = Field(
        ...,
        title="Error URL",
    )


class ValidationError(RootModel):
    """Model of a validation error response."""

    root: Sequence[ValidationErrorElement]


class SecureType(str, Enum):
    HTTP = "http"
    API_KEY = "apiKey"
    OAUTH_TWO = "oauth2"
    OPEN_ID_CONNECT = "openIdConnect"


class InType(str, Enum):
    HEADER = "header"
    QUERY = "query"
    COOKIE = "cookie"


type_req_fields: Dict[SecureType, Sequence[str]] = {
    SecureType.HTTP: ["scheme"],
    SecureType.API_KEY: ["name", "in"],
    SecureType.OAUTH_TWO: ["flows"],
    SecureType.OPEN_ID_CONNECT: ["openIdConnectUrl"],
}


class SecuritySchemeData(BaseModel):
    """
    Security scheme data
    https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#securitySchemeObject
    """

    type: SecureType = Field(..., description="Secure scheme type")
    description: Optional[str] = Field(
        None,
        description="A short description for security scheme.",
    )
    name: Optional[str] = Field(
        None,
        description="The name of the header, query or cookie parameter to be used.",
    )
    field_in: Optional[InType] = Field(
        None, alias="in", description="The location of the API key."
    )
    scheme: Optional[str] = Field(
        None, description="The name of the HTTP Authorization scheme."
    )
    bearerFormat: Optional[str] = Field(
        None,
        description=(
            "A hint to the client to identify how the bearer token is formatted."
        ),
    )
    flows: Optional[dict] = Field(
        None,
        description=(
            "Containing configuration information for the flow types supported."
        ),
    )
    openIdConnectUrl: Optional[str] = Field(
        None, description="OpenId Connect URL to discover OAuth2 configuration values."
    )

    model_config = ConfigDict(validate_assignment=True)

    @model_validator(mode="before")
    def check_type_required_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        exist_fields = {key for key in values.keys() if values[key]}
        if not values.get("type"):
            raise ValueError("Type field is required")

        if not set(type_req_fields[values["type"]]).issubset(exist_fields):
            raise ValueError(
                f"For `{values['type']}` type "
                f"`{', '.join(type_req_fields[values['type']])}` field(s) is required."
            )
        return values


class SecurityScheme(BaseModel):
    """
    Named security scheme
    """

    name: str = Field(
        ...,
        description="Custom security scheme name. Can only contain - [A-Za-z0-9-._]",
    )
    data: SecuritySchemeData = Field(..., description="Security scheme data")

    model_config = ConfigDict(validate_assignment=True)

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str):
        if not OpenAPI_NAME_RE.fullmatch(value):
            raise ValueError("Name not match OpenAPI rules")
        return value


class Server(BaseModel):
    """
    Servers section of OAS
    """

    url: str = Field(
        ...,
        description="""URL or path of API server

        (may be parametrized with using \"variables\" section - for more information,
        see: https://swagger.io/docs/specification/api-host-and-base-path/ )""",
    )
    description: Optional[str] = Field(
        None,
        description="Custom server description for server URL",
    )
    variables: Optional[dict] = Field(
        None,
        description="Variables for customizing server URL",
    )

    model_config = ConfigDict(validate_assignment=True)


class BaseFile:
    """
    An uploaded file included as part of the request data.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _source: Any) -> core_schema.CoreSchema:
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        return core_schema.general_plain_validator_function(cls.validate)

    def __get_pydantic_json_schema__(cls, *args) -> JsonSchemaValue:
        field_schema = {"format": "binary", "type": "string"}
        return field_schema

    @classmethod
    def validate(cls, value: Any, info: core_schema.ValidationInfo) -> Any:
        # https://github.com/luolingchun/flask-openapi3/blob/master/flask_openapi3/models/file.py
        return value
