import os
import firebase_admin
from firebase_admin import credentials

path = os.getenv("FIREBASE_CREDENTIALS")

cred = credentials.Certificate(path)
firebase_admin.initialize_app(cred)
