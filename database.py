import json
import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_SERVICE_ACCOUNT_JSON


def _load_credential():
    value = FIREBASE_SERVICE_ACCOUNT_JSON
    if not value:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다.")
    # Render 배포: JSON 내용 전체가 들어있는 경우
    if value.strip().startswith("{"):
        return credentials.Certificate(json.loads(value))
    # 로컬: 파일 경로가 들어있는 경우
    return credentials.Certificate(value)


if not firebase_admin._apps:
    firebase_admin.initialize_app(_load_credential())

db = firestore.client()