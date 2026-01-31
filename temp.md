import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import os
os.environ['REQUESTS_CA_BUNDLE'] = ''


def get_access_token():
    """Authenticate using interactive browser login"""
    from azure.identity import InteractiveBrowserCredential
    import ssl

    print("🔐 Opening browser for authentication...")
    
    # Create SSL context that doesn't verify certificates
    ssl_context = ssl._create_unverified_context()
    
    credential = InteractiveBrowserCredential()
    token = credential.get_token(POWER_BI_SCOPE)
    print("✅ Authentication successful!")
    return token.token
