from fastapi import APIRouter, Response
import pandas as pd
from app import db
import io
from datetime import datetime
import urllib.parse

router = APIRouter(prefix="/api/export", tags=["Excel Export"])

@router.get("/{target}")
async def export_excel(target: str):
    try:
        # 1. 데이터 가져오기 및 파일명 설정
        if target == "inventory":
            data = db.get_inventory()
            base_name = "재고현황"
        elif target == "history":
            data = db.get_history_for_excel()
            base_name = "작업이력"
        else:
            return Response(content="잘못된 요청입니다.", status_code=400)

        if not data:
            return Response(content="출력할 데이터가 없습니다.", status_code=404)

        # 2. Pandas를 이용한 엑셀 파일 생성
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        # 3. 한글 파일명 안전하게 인코딩 (urllib 사용)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"{base_name}_{timestamp}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        # 4. HTTP 응답 구성 (한글 파일명 호환 헤더 추가)
        headers = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
        
        return Response(
            content=output.getvalue(), 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            headers=headers
        )
    except Exception as e:
        # 에러 발생 시 상세 내용을 브라우저에 표시
        return Response(content=f"엑셀 생성 중 에러 발생: {str(e)}", status_code=500)
