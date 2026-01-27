"""Authentication module for SmartThings Find integration.

This module implements the OAuth2 authentication flow based on the uTag implementation.
"""

import logging
import json
import base64
import hashlib
import secrets
import string
from typing import Dict, Tuple, Optional
from urllib.parse import urlencode, quote, parse_qs

import aiohttp
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import serialization

_LOGGER = logging.getLogger(__name__)

# Constants from uTag documentation
CLIENT_ID = "yfrtglt53o"
REDIRECT_URI = "ms-app://s-1-15-2-4027708247-2189610-1983755848-2937435718-1578786913-2158622839-1974417358"
FIND_CLIENT_ID = "27zmg0v1oo"
FIND_SCOPE = "offline.access"
SMARTTHINGS_CLIENT_ID = "6iado3s6jc"
SMARTTHINGS_SCOPE = "iot.client"

# URLs
ENTRY_POINT_URL = "https://account.samsung.com/accounts/ANDROIDSDK/getEntryPoint"
SIGNIN_GATE_URL = "https://account.samsung.com/accounts/ANDROIDSDK/signInGate"


def generate_code_challenge() -> Tuple[str, str]:
    """Generate PKCE code challenge and verifier.
    
    Returns:
        Tuple of (code_challenge, code_verifier)
    """
    code_verifier = secrets.token_urlsafe(43)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    return code_challenge, code_verifier


def generate_state() -> str:
    """Generate random state string."""
    return secrets.token_urlsafe(20)


def encrypt_payload(payload: Dict, pki_public_key: str, chk_do_num: str) -> Tuple[str, str, str]:
    """Encrypt the SVC payload.
    
    Args:
        payload: Dictionary containing the SVC parameters
        pki_public_key: Base64 encoded public key
        chk_do_num: Check number for encryption
        
    Returns:
        Tuple of (svc_enc_ky, svc_enc_param, svc_enc_iv)
    """
    try:
        # Hash chk_do_num
        chk_hash = hashlib.sha256(chk_do_num.encode()).digest()
        chk_hash_b64 = base64.b64encode(chk_hash).decode()
        
        # Generate random key
        key = secrets.token_bytes(16)
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=key,
            iterations=int(chk_do_num),
            backend=default_backend()
        )
        derived_key = kdf.derive(chk_hash)
        
        # Encrypt derived key with RSA public key
        public_key_bytes = base64.b64decode(pki_public_key)
        public_key = serialization.load_der_public_key(public_key_bytes, backend=default_backend())
        
        encrypted_key = public_key.encrypt(
            derived_key,
            asym_padding.PKCS1v15()
        )
        svc_enc_ky = base64.b64encode(encrypted_key).decode()
        
        # Generate IV and encrypt payload
        iv = secrets.token_bytes(16)
        cipher = Cipher(
            algorithms.AES(derived_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Convert payload to JSON and pad
        payload_json = json.dumps(payload, separators=(',', ':'))
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(payload_json.encode()) + padder.finalize()
        
        encrypted_payload = encryptor.update(padded_data) + encryptor.finalize()
        svc_enc_param = base64.b64encode(encrypted_payload).decode()
        svc_enc_iv = iv.hex()
        
        return svc_enc_ky, svc_enc_param, svc_enc_iv
        
    except Exception as e:
        _LOGGER.error(f"Failed to encrypt payload: {e}")
        raise


def create_svc_payload(code_challenge: str, state: str) -> Dict:
    """Create the SVC payload for authentication.
    
    Args:
        code_challenge: PKCE code challenge
        state: Random state string
        
    Returns:
        Dictionary containing SVC parameters
    """
    return {
        "clientId": CLIENT_ID,
        "codeChallenge": code_challenge,
        "codeChallengeMethod": "S256",
        "competitorDeviceYNFlag": "Y",
        "countryCode": "us",
        "deviceInfo": "Google|com.android.chrome",
        "deviceModelId": "Home Assistant",
        "deviceName": "Home Assistant",
        "deviceOSVersion": "2024.1",
        "devicePhysicalAddressText": f"ANID:{secrets.token_hex(16)}",
        "deviceType": "APP",
        "deviceUniqueId": "ANID",
        "redirectUri": REDIRECT_URI,
        "replaceableClientConnectYN": "N",
        "responseEncryptionType": "1",
        "responseEncryptionYNFlag": "Y",
        "scope": "",
        "state": state,
        "svcIptLgnID": "",
        "iosYNFlag": "Y"
    }


async def get_entry_point(session: aiohttp.ClientSession) -> Dict:
    """Get the entry point for authentication.
    
    Args:
        session: aiohttp session
        
    Returns:
        Dictionary containing entry point data
        
    Raises:
        Exception: If request fails
    """
    async with session.get(ENTRY_POINT_URL) as response:
        if response.status != 200:
            raise Exception(f"Failed to get entry point: {response.status}")
        
        data = await response.json()
        _LOGGER.debug(f"Entry point response: {data}")
        return data


def create_signin_url(entry_point: Dict, code_challenge: str, state: str) -> Tuple[str, str, str, str]:
    """Create the sign-in URL with encrypted payload.
    
    Args:
        entry_point: Entry point data
        code_challenge: PKCE code challenge  
        state: Random state string
        
    Returns:
        Tuple of (signin_url, code_verifier, state, chk_do_num)
    """
    # Extract required data from entry point
    sign_in_uri = entry_point["signInURI"]
    pki_public_key = entry_point["pkiPublicKey"]
    chk_do_num = entry_point["chkDoNum"]
    
    # Create SVC payload
    svc_payload = create_svc_payload(code_challenge, state)
    
    # Encrypt payload
    svc_enc_ky, svc_enc_param, svc_enc_iv = encrypt_payload(
        svc_payload, pki_public_key, chk_do_num
    )
    
    # Create URL parameters
    params = {
        "locale": "en",
        "svcParam": urlencode({
            "chkDoNum": chk_do_num,
            "svcEncParam": svc_enc_param,
            "svcEncKY": svc_enc_ky,
            "svcKeyIV": svc_enc_iv
        }),
        "mode": "C"
    }
    
    # Build final URL
    signin_url = f"{sign_in_uri}?{urlencode(params)}"
    
    return signin_url, state, chk_do_num


def decrypt_response(encrypted_data: str, state: str, chk_do_num: str) -> Dict:
    """Decrypt the authentication response.
    
    Args:
        encrypted_data: Base64 encrypted response data
        state: Original state string
        chk_do_num: Check number used for encryption
        
    Returns:
        Decrypted response data
    """
    try:
        # Derive decryption key
        state_hash = hashlib.sha256(state.encode()).digest()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=state.encode(),
            iterations=int(chk_do_num),
            backend=default_backend()
        )
        key = kdf.derive(state_hash)
        
        # Decode and decrypt
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Extract IV (first 16 bytes)
        iv = encrypted_bytes[:16]
        ciphertext = encrypted_bytes[16:]
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return json.loads(data.decode())
        
    except Exception as e:
        _LOGGER.error(f"Failed to decrypt response: {e}")
        raise


async def get_user_auth_token(
    session: aiohttp.ClientSession,
    auth_server_url: str,
    code: str,
    code_verifier: str,
    physical_address: str
) -> Dict:
    """Get user auth token from authorization code.
    
    Args:
        session: aiohttp session
        auth_server_url: Authentication server URL
        code: Authorization code
        code_verifier: PKCE code verifier
        physical_address: Physical address for authentication
        
    Returns:
        Dictionary containing user auth token data
    """
    url = f"{auth_server_url}/auth/oauth2/v2/authorize"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "code_verifier": code_verifier,
        "serviceType": "M",
        "username": "",
        "physical_address_text": f"ANID:{physical_address}"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    async with session.post(url, data=data, headers=headers) as response:
        if response.status != 200:
            raise Exception(f"Failed to get user auth token: {response.status}")
        
        token_data = await response.json()
        _LOGGER.debug(f"User auth token response: {token_data}")
        return token_data


async def get_api_token(
    session: aiohttp.ClientSession,
    auth_server_url: str,
    user_auth_token: str,
    client_id: str,
    scope: str
) -> Dict:
    """Get API token for Find or SmartThings API.
    
    Args:
        session: aiohttp session
        auth_server_url: Authentication server URL
        user_auth_token: User authentication token
        client_id: Client ID for the API
        scope: Scope for the API
        
    Returns:
        Dictionary containing API token data
    """
    url = f"{auth_server_url}/auth/oauth2/v2/token"
    
    data = {
        "grant_type": "user_auth_token",
        "client_id": client_id,
        "user_auth_token": user_auth_token,
        "scope": scope
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    async with session.post(url, data=data, headers=headers) as response:
        if response.status != 200:
            raise Exception(f"Failed to get API token: {response.status}")
        
        token_data = await response.json()
        _LOGGER.debug(f"API token response for {client_id}: {token_data}")
        return token_data


async def complete_smartthings_login(
    session: aiohttp.ClientSession,
    api_token: str
) -> str:
    """Complete login to SmartThings Find service.
    
    Args:
        session: aiohttp session
        api_token: API token for SmartThings Find
        
    Returns:
        JSESSIONID for SmartThings Find
    """
    # This would complete the login flow and get the JSESSIONID
    # Implementation would depend on the exact SmartThings Find login flow
    # For now, this is a placeholder that would need to be implemented
    # based on the actual API calls needed
    
    # The current implementation uses the JSESSIONID directly from the browser
    # In the new implementation, we'd need to exchange the API token for
    # a session cookie with SmartThings Find
    
    raise NotImplementedError(
        "SmartThings Find login completion needs to be implemented "
        "based on the actual API flow"
    )
