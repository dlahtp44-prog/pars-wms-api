from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app import db

# 프리픽스를 통합 (프론트엔드 버튼의 /api/export_excel/ 경로와 일치시킴)
router = APIRouter(prefix="/api/export_excel", tags=["Export"])

@router.get("/inventory")
async def export_inventory():
    """현재 재고 현황 엑셀 다운로드"""
    try:
        data = db.get_inventory()
        if not data:
            raise HTTPException(status_code=404, detail="데이터가 없습니다.")
            
        df = pd.DataFrame(data)
        
        # 컬럼명 한글 변환 (spec 포함)
        column_map = {
            'warehouse': '창고', 
            'location': '로케이션', 
            'item_code': '품번',
            'item_name': '품명', 
            'lot_no': 'LOT', 
            'spec': '규격', 
            'qty': '수량', 
            'updated_at': '업데이트일시'
        }
        df = df.rename(columns=column_map)
        
        # 출력 순서 정의
        cols = ['창고', '로케이션', '품번', '품명', 'LOT', '규격', '수량', '업데이트일시']
        df = df[[c for c in cols if c in df.columns]]

        output = io.BytesIO()
        # xlsxwriter 엔진을 사용하여 엑셀 생성
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='현재고')
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=inventory_report.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def export_history():
    """작업 이력 전체 엑셀 다운로드"""
    try:
        data = db.get_history()
        if not data:
            raise HTTPException(status_code=404, detail="이력 데이터가 없습니다.")
            
        df = pd.DataFrame(data)
        
        # 이력 테이블 컬럼 매핑
        column_map = {
            'created_at': '작업일시',
            'tx_type': '유형',
            'item_code': '품번',
            'item_name': '품명',
            'lot_no': 'LOT',
            'spec': '규격',
            'qty': '수량',
            'location': '로케이션',
            'from_location': '이전위치',
            'to_location': '이동위치',
            'remark': '비고'
        }
        df = df.rename(columns=column_map)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='작업이력')
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=wms_history.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
