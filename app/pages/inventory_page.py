# 테이블 헤더 부분에 '규격' 추가
"""
<thead>
    <tr>
        <th>창고</th>
        <th>로케이션</th>
        <th>품번</th>
        <th>품명</th>
        <th>LOT</th>
        <th>규격</th>  <th>수량</th>
    </tr>
</thead>
<tbody>
"""

# 데이터 출력 부분에 '규격' 추가
"""
for row in rows:
    <tr>
        <td>{row['warehouse']}</td>
        <td><span class="badge bg-secondary">{row['location']}</span></td>
        <td>{row['item_code']}</td>
        <td>{row['item_name']}</td>
        <td>{row['lot_no']}</td>
        <td>{row['spec']}</td>  <td class="fw-bold text-primary">{row['qty']}</td>
    </tr>
"""
