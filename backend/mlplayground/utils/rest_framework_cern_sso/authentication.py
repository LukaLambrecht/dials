from typing import Optional, Tuple

from django.conf import settings
from rest_framework.request import Request
from rest_framework.authentication import BaseAuthentication

from .backends import CERNKeycloakOIDC
from .token import CERNKeycloakToken
from .user import CERNKeycloakUser
from .exceptions import AuthenticationFailed

try:
    from .schemes import *  # noqa: F401
except ImportError:
    pass

public_kc = CERNKeycloakOIDC(
    server_url=settings.KEYCLOAK_SERVER_URL,
    client_id=settings.KEYCLOAK_PUBLIC_CLIENT_ID,
    realm_name=settings.KEYCLOAK_REALM,
)

confidential_kc = CERNKeycloakOIDC(
    server_url=settings.KEYCLOAK_SERVER_URL,
    client_id=settings.KEYCLOAK_CONFIDENTIAL_CLIENT_ID,
    client_secret_key=settings.KEYCLOAK_CONFIDENTIAL_SECRET_KEY,
    realm_name=settings.KEYCLOAK_REALM,
)

api_clients_kc = {
    client_secret_key: CERNKeycloakOIDC(
        server_url=settings.KEYCLOAK_SERVER_URL,
        client_id=client_id,
        client_secret_key=client_secret_key,
        realm_name=settings.KEYCLOAK_REALM,
    )
    for client_secret_key, client_id in settings.KEYCLOAK_API_CLIENTS.items()
}


class CERNKeycloakClientSecretAuthentication(BaseAuthentication):
    """
    Custom authentication class based on CERN's Keycloak Api Access.

    This authentication flow is solely for authenticating using other confidential clients secret key.
    Those clients must have configured the option "My application will need to get tokens using its own client ID and secret".

    What is the use case?
        * Automated scripts that needs non-interactively authentication

    Why not use this authentication for human-users access the api?
        * Because the token generated from "Api Access" do not carry the user information,
        it instead carry general information from the client. That means the users are indistinguishable,
        so you cannot rely on roles unless you create multiple clients for specific roles.
        * Also it is very insecure, because users would share the same secret,
        if one leaks you need to notify all users that you changing the secret key. You could circumvent
        this creating one client per user but that would generate a tons of clients
        and you would also need to clean old clients when users leave cern and loose access to the application.
    """
    HEADER_KEY = "X-CLIENT-SECRET"

    def authenticate(self, request: Request) -> Optional[Tuple[CERNKeycloakUser, CERNKeycloakToken]]:
        secret_key = self.get_secret_key(request.headers)

        # Returning None since Django's multi authentication logic
        # works if all N-1 ordered authentication classes
        # return None instead of raising an error
        if secret_key is None:
            return None

        if secret_key not in api_clients_kc:
            raise AuthenticationFailed(
                "App secret is not authorized."
                "app_secret_not_authorized"
            )

        kc: CERNKeycloakOIDC = api_clients_kc[secret_key]
        issued_token = kc.issue_api_token()
        token = CERNKeycloakToken(issued_token["access_token"], kc)

        # We don't need to `validate` because the token was just generated
        # patching the token class for the user class appear validated
        token.is_authenticated = True
        token.claims = token.unv_claims

        return CERNKeycloakUser(token), token

    def get_secret_key(self, headers: dict) -> str:
        return headers.get(self.HEADER_KEY)


class CERNKeycloakBearerAuthentication(BaseAuthentication):
    """
    Custom authentication class based on CERN's Keycloak Bearer Token.

    This authentication flow must be configured using the argument `expected_bearer_token_type`.
    For the public client, it only checks the public aud and azp.
    For the confidential client, it checks only for the confidential aud and for both public and confidential azp.

    What is the use case?
        * Public tokens **should only** authenticate **in a specific token exchange route**
        in order to receive a confidential token
        * Confidential tokens can authenticate in any other route
        but we need to make sure that the token was generated by the confidential client
        or exchanged from the public client

    Note: Confidential tokens are generated from the confidential client
    if someone uses a script for the general token endpoint
    and interactively sign-on via the totp (password) flow or device flow
    """
    HEADER_KEY = "Authorization"

    def authenticate(self, request: Request) -> Optional[Tuple[CERNKeycloakUser, CERNKeycloakToken]]:
        access_token = self.get_access_token(request.headers)
        kc, valid_aud, valid_azp = self.get_kc_by_expected_token()
        token = CERNKeycloakToken(access_token, kc)
        token.validate(valid_aud, valid_azp)
        return CERNKeycloakUser(token), token

    def get_kc_by_expected_token(self):
        if self.expected_bearer_token_type == "public":
            valid_aud = [settings.KEYCLOAK_PUBLIC_CLIENT_ID]
            valid_azp = [settings.KEYCLOAK_PUBLIC_CLIENT_ID]
            kc = public_kc
        elif self.expected_bearer_token_type == "confidential":
            valid_aud = [settings.KEYCLOAK_CONFIDENTIAL_CLIENT_ID]
            valid_azp = [settings.KEYCLOAK_CONFIDENTIAL_CLIENT_ID, settings.KEYCLOAK_PUBLIC_CLIENT_ID]
            kc = confidential_kc
        else:
            raise ValueError("expected_bearer_token_type should only be public or confidential.")

        return kc, valid_aud, valid_azp

    def get_access_token(self, headers: dict) -> str:
        try:
            bearer = headers[self.HEADER_KEY]
        except KeyError:
            raise AuthenticationFailed(
                "Authorization header not found.",
                "authorization_not_found"
            )

        try:
            return bearer.split("Bearer ")[-1]
        except AttributeError:
            raise AuthenticationFailed(
                "Malformed access token.",
                "bad_access_token"
            )


class CERNKeycloakPublicAuthentication(CERNKeycloakBearerAuthentication):
    """
    Custom authentication class based on `CERNKeycloakBearerAuthentication` that
    will only authenticate tokens generated by the public client.
    """

    def __init__(self):
        super().__init__()
        self.expected_bearer_token_type = "public"


class CERNKeycloakConfidentialAuthentication(CERNKeycloakBearerAuthentication):
    """
    Custom authentication class based on `CERNKeycloakBearerAuthentication` that
    will only authenticate tokens generated by the confidential client or
    generated by the public client and later exchanged with the confidential client.
    """

    def __init__(self):
        super().__init__()
        self.expected_bearer_token_type = "confidential"
