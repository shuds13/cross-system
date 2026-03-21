from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc7523 import PrivateKeyJWT

token_url = "https://oidc.nersc.gov/c2id/token"

with open("clientid.txt") as f:
    client_id = f.read().strip()

with open("priv_key.pem") as f:
    private_key = f.read()

session = OAuth2Session(
    client_id,
    private_key,
    PrivateKeyJWT(token_url),
    grant_type="client_credentials",
    token_endpoint=token_url,
)

token = session.fetch_token()
print(token["access_token"])
