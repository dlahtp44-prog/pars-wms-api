@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    df.columns = [c.strip() for c in df.columns]
    
    for _, row in df.iterrows():
        db.add_inventory(
            warehouse=str(row['창고']),
            location=str(row['로케이션']),
            item_code=str(row['품번']),
            item_name=str(row['품명']),
            lot_no=str(row['LOT']),
            spec=str(row.get('규격', '-')), # 규격 추가
            qty=float(row['수량']),
            remark="엑셀 일괄입고"
        )
    return {"message": "입고 및 작업로그 기록 완료"}
