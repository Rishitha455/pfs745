from itsdangerous import URLSafeTimedSerializer
from key import salt
def encode(data):
    seralizer=URLSafeTimedSerializer('code@123')
    return seralizer.dumps(data,salt=salt)
def decode(data):
    seralizer=URLSafeTimedSerializer('code@123')
    return seralizer.loads(data,salt=salt)