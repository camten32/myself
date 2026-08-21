import os
import io
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from PIL import Image
import torch
import torch.nn as nn
from torchvision import transforms, models
from fastapi import Depends
from core.auth import get_current_user, check_user_role
from models import User, UserRole



router = APIRouter(
    prefix="/prediction",
    tags=["prediction"]
)

# 1. 디바이스 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 2. 노트북과 동일한 모델 생성 함수
def create_resnet50_model():
    model = models.resnet50(weights=None)
    num_ftrs = model.fc.in_features
    # 드롭아웃이 포함된 FC 레이어 구조 재정의
    model.fc = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(num_ftrs, 2)
    )
    return model.to(device)

# 3. 전처리 파이프라인 (학습/테스트 시 사용하던 설정)
normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
tf_transfer = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Lambda(lambda x: x.repeat(3, 1, 1)), # 1채널을 3채널로 복제
    normalize
])

# 4. 저장된 .pth (또는 .pkl) 가중치 파일 로드
# 저장해두신 파일 경로를 정확히 입력해 주세요. (예: 'model_weights/data.pkl' 또는 'model_weights/best_model.pth')
MODEL_PATH = r"D:\Download\model_weights.pth"

model = create_resnet50_model()

if os.path.exists(MODEL_PATH):
    # weights/state_dict 로드
    state_dict = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()  # 평가 모드로 전환 (Dropout, BatchNorm 동결)
    print(f" 성공적으로 모델 가중치를 로드했습니다: {MODEL_PATH}")
else:
    print(f" 경고: 모델 가중치 파일({MODEL_PATH})을 찾을 수 없습니다.")


# 5. 실제 예측에 사용할 함수
def predict_image(image: Image.Image):
    """
    PIL Image 객체를 받아 예측 결과(클래스 인덱스, 확률)를 반환하는 함수
    """
    # 전처리 적용 및 배치 차원 추가 (1, C, H, W)
    input_tensor = tf_transfer(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted_class = torch.max(probabilities, 1)
        
    return predicted_class.item(), confidence.item()


# Google Gemini API 설정

load_dotenv()

# 3. 환경 변수에서 키 꺼내기
api_key = os.getenv("api_key")

genai.configure(api_key=api_key)

async def get_health_advice(prediction_result: int, confidence: float, patient_lifestyle: str):
    status_text = "폐렴 위험이 있음" if prediction_result == 1 else "정상"
    
    prompt = f"""
    당신은 전문 의사입니다. 다음 정보를 바탕으로 환자에게 생활 습관 및 식습관 조언을 해주세요.
    - 진단 결과: {status_text} (신뢰도: {confidence * 100:.2f}%)
    - 환자의 생활 패턴: {patient_lifestyle}
    
    위 데이터를 분석하여, 폐 건강을 지키기 위한 구체적인 생활 가이드와 식단 추천을 친절하게 작성해주세요.
    """
    
    model = genai.GenerativeModel('gemini-3.6-flash')
    response = model.generate_content(prompt)
    return response.text


allow_medical_staff = check_user_role([UserRole.Doctor, UserRole.Nurse, UserRole.Admin])



@router.post("/", summary="이미지 분석 및 예측", status_code=status.HTTP_200_OK)
async def predict_api(
    file: UploadFile = File(...),
    current_user: User = Depends(allow_medical_staff)
    ):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 파일만 업로드 가능합니다."
        )
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        pred_class, confidence = predict_image(image)
        

        lifestyle = getattr(current_user, 'lifestyle', '규칙적인 생활을 하는 편입니다.')

        advice = await get_health_advice(int(pred_class), float(confidence), lifestyle)
        

        return {
            "filename": file.filename,
            "predicted_class": int(pred_class),
            "confidence": round(float(confidence), 4),
            "advice": advice  # <-- AI가 생성한 조언 추가!
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예측 처리 중 오류 발생: {str(e)}"
        )


