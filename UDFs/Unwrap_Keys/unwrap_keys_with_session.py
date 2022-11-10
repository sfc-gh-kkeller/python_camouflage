import json
import base64
import binascii
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Protocol.KDF import PBKDF2
import zlib
import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import traceback
from base64 import b64encode, b64decode

from Crypto.Hash import SHA256, SHA512
from Crypto.PublicKey import RSA
from hashlib import sha512

from Crypto.Signature import pkcs1_15





BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]



def get_private_key(password):
    salt = b"this is a salt"
    kdf = PBKDF2(password, salt, 64, 1000)
    key = kdf[:32]
    return key


def encrypt(raw, password):
    private_key = get_private_key(password)
    raw = pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    #print (binascii.hexlify(private_key).decode("utf-8"))
    return base64.b64encode(iv + cipher.encrypt(raw.encode("utf8")))


def decrypt(enc, password):
    private_key = get_private_key(password)
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[16:]))
    
    
#JWT stuff

jwks_string=''
jwks={}


def ensure_bytes(key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    return key


def decode_value(val):
    decoded = base64.urlsafe_b64decode(ensure_bytes(val) + b'==')
    return int.from_bytes(decoded, 'big')


def rsa_pem_from_jwk(jwk):
    return RSAPublicNumbers(
        n=decode_value(jwk['n']),
        e=decode_value(jwk['e'])
    ).public_key(default_backend()).public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


valid_audiences = ['https://kelleruserflow.snowflakeseclab42outlook.onmicrosoft.com'] # id of the application prepared previously
issuer = 'https://sts.windows.net/b3b06c45-b6f1-4d13-a720-8845b509b948/' # iss


class InvalidAuthorizationToken(Exception):
    def __init__(self, details):
        super().__init__('Invalid authorization token: ' + details)


def get_kid(token):
    headers = jwt.get_unverified_header(token)
    if not headers:
        raise InvalidAuthorizationToken('missing headers')
    try:
        return headers['kid']
    except KeyError:
        raise InvalidAuthorizationToken('missing kid')


def get_jwk(kid,jwks):
    for jwk in jwks.get('keys'):
        if jwk.get('kid') == kid:
            return jwk
    raise InvalidAuthorizationToken('kid not recognized')


def get_public_key(token,jwks):
    return rsa_pem_from_jwk(get_jwk(get_kid(token),jwks))


def validate_jwt(jwt_to_validate,jwks):
    public_key = get_public_key(jwt_to_validate,jwks)

    decoded = jwt.decode(jwt_to_validate,
                         public_key,
                         verify=True,
                         algorithms=['RS256'],
                         audience=valid_audiences,
                         issuer=issuer)

    # do what you wish with decoded token:
    # if we get here, the JWT is validated
    #print(decoded)


def generate_aes_key(jwt_to_validate,jwks,sig):
    public_key = get_public_key(jwt_to_validate,jwks)

    decoded = jwt.decode(jwt_to_validate,
                         public_key,
                         verify=True,
                         algorithms=['RS256'],
                         audience=valid_audiences,
                         issuer=issuer)

    # do what you wish with decoded token:
    # if we get here, the JWT is validated
    # print(decoded)

    password = ''
    password = str(decoded['exp']) + str(decoded['upn'])+sig
    #password = str(decoded['exp']) + str(decoded['sub'])+sig
    message = password
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')
    return (base64_message)
    
def get_user_from_token(jwt_to_validate,jwks):
    public_key = get_public_key(jwt_to_validate,jwks)

    decoded = jwt.decode(jwt_to_validate,
                         public_key,
                         verify=True,
                         algorithms=['RS256'],
                         audience=valid_audiences,
                         issuer=issuer)

    # do what you wish with decoded token:
    # if we get here, the JWT is validated
    # print(decoded)


    #(str(decoded['sub']))
    return (str(decoded['upn']))

    def get_groups_from_token(jwt_to_validate,jwks):
    public_key = get_public_key(jwt_to_validate,jwks)

    decoded = jwt.decode(jwt_to_validate,
                         public_key,
                         verify=True,
                         algorithms=['RS256'],
                         audience=valid_audiences,
                         issuer=issuer)

    # do what you wish with decoded token:
    # if we get here, the JWT is validated
    # print(decoded)


    #(str(decoded['sub']))
    return (str(decoded['groups']))
    
def verify_session(pubkey,session, signature):
    cryptor = RSA.importKey(pubkey)
    message = session
    digest = SHA256.new(message.encode("utf-8"))
    
    try:
        pkcs1_15.new(cryptor).verify(digest, base64.b64decode(signature))
        return True
    except (ValueError, TypeError):
        return False
    
    


    


def udf(key, userkeys, tokencompress, a, currentuser, currentsession, sessionkey):

    jwtks=zlib.decompress(a).decode()
    jwtks=jwtks.replace('\\"','"')
    jwtks=jwtks[2:]
    jwtks=jwtks[:-2]
    jwks_string=jwtks

    jwt_valid=False
    jwks=json.loads(jwks_string)

    #jwt = token
    
    tokenwithsig=zlib.decompress(tokencompress).decode()
    tokenseparated=tokenwithsig.split('SIG')
    token=tokenseparated[0]
    signature=tokenseparated[1]


    try:
        validate_jwt(token,jwks)
    except Exception as ex:
        traceback.print_exc()
        jwt_valid=False
    else:
        jwt_valid=True
    sessionkey=sessionkey.replace("'","")
    valid=False
    valid=verify_session( sessionkey, currentsession,signature)
    
        
    if jwt_valid==True and valid==True:
        user=get_user_from_token(token,jwks)
        if user.upper()==currentuser:
            password=generate_aes_key(token,jwks,signature)
        else:
            return('current user does not match token or session not allowed')
   
        
    


    #encrypted=str(userkeys['678901'])
    userkeys=userkeys.replace('}{',',')
    userkey_json=json.loads(userkeys)
    key=key[3:]
    encrypted=str(userkey_json[key])
    #password=generate_aes_key(token,jwks)
    decrypted = decrypt(encrypted, password)
    #print(bytes.decode(decrypted))
    result=str(bytes.decode(decrypted))
    result=result.replace('\\','')
    result=result.replace('"}','}')
    result=result.replace(':"[',':[')
    return result

