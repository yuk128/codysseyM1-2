# 서울 기온 AI 비서

서울 일별 기온 데이터(2023-01-01 ~ 2024-12-31, 731건)를 분석한 요약을 AI의 시스템 프롬프트에 주입(컨텍스트 주입)해서, 저장된 데이터를 바탕으로 답해 주는 AI 비서 웹 서비스입니다. 데이터 CRUD, 대화 기록 저장/불러오기를 지원합니다.

## 기술 스택

- 백엔드: FastAPI, Pydantic
- 데이터베이스: Firebase Firestore
- AI: Google Gemini API (OpenAI 호환 엔드포인트, `openai` 패키지 사용). 모델은 환경변수 `GEMINI_MODEL`로 지정
- 프론트엔드: 바닐라 HTML/CSS/JavaScript
- 배포: Render(백엔드), Vercel(프론트엔드)

## 배포 URL

- 프론트엔드: https://codysseym1-2-frontend.vercel.app
- 백엔드 API: https://codysseym1-2.onrender.com
- Swagger UI: https://codysseym1-2.onrender.com/docs

> 백엔드는 Render 무료 서버라서 15분간 요청이 없으면 잠듭니다. 이후 첫 요청은 최대 약 1분 걸릴 수 있습니다.

## 데이터

- 출처/내용: 서울 일별 기온 (평균/최고/최저)
- 기간: 2023-01-01 ~ 2024-12-31, 총 731건
- 저장 형태: `date`(날짜), `value`(평균기온), `memo`(최고/최저 기온)

## 로컬 실행 방법

```powershell
# 1. 가상환경 및 패키지
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. .env 파일 작성 (아래 환경변수 목록 참고)

# 3. 백엔드 실행 (터미널 1)
uvicorn main:app --reload

# 4. 프론트 실행 (터미널 2) -> http://localhost:5500
python -m http.server 5500 --directory frontend
```

프론트가 호출하는 백엔드 주소는 `frontend/config.js`의 `API_BASE_URL`에서 바꿀 수 있습니다. 로컬 백엔드를 쓰려면 `http://localhost:8000`으로 설정하세요.

## 환경변수 목록

| 이름 | 설명 |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 |
| `GEMINI_MODEL` | 사용할 Gemini 모델 이름 |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | 서비스 계정 키 (로컬은 파일 경로, 배포는 JSON 내용) |
| `ALLOWED_ORIGINS` | CORS 허용 주소 (쉼표로 구분) |

## API 요약

- 데이터: `GET /api/data/summary`, `GET /api/data`, `POST /api/data`, `PUT /api/data/{id}`, `DELETE /api/data/{id}`
- 대화: `POST /api/conversations`, `GET /api/conversations`, `GET /api/conversations/{id}`, `DELETE /api/conversations/{id}`
- 챗봇: `POST /api/chat`