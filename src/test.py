from oauthenticator.generic import GenericOAuthenticator


def main():
    auth = GenericOAuthenticator()
    print(auth.http_client)
    print(auth.username_key)
    print(auth.extra_params)
    print(auth.tls_verify)


if __name__ == "__main__":
    main()
