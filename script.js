document.addEventListener('DOMContentLoaded', () => {
  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');
  const resultsDiv = document.getElementById('results');

  searchBtn.addEventListener('click', async () => {
    const query = searchInput.value.trim();
    if (!query) {
      resultsDiv.innerHTML = '<p style="color:red;">검색어를 입력하세요.</p>';
      return;
    }
    
    resultsDiv.innerHTML = '<p>검색 중...</p>';
    
    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, top_k: 3 })
      });
      
      const data = await response.json();
      
      let html = `<p><strong>의도 분석:</strong> ${data.intent_info.intent} (신뢰도: ${(data.intent_info.confidence * 100).toFixed(1)}%)</p>`;
      html += `<p style="color: #666;"><em>${data.message}</em></p>`;
      
      if (data.results && data.results.length > 0) {
        html += '<ul style="list-style-type: none; padding: 0;">';
        data.results.forEach(item => {
          html += `<li style="margin-bottom: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 5px;">
            <strong>[순위 ${item.rank} / 거리 ${item.distance}]</strong><br>
            ${item.description}
          </li>`;
        });
        html += '</ul>';
      }
      
      resultsDiv.innerHTML = html;
      
    } catch (error) {
      console.error(error);
      resultsDiv.innerHTML = '<p style="color:red;">서버와 연결할 수 없습니다. (FastAPI 백엔드가 실행 중인지 확인하세요)</p>';
    }
  });

  // 엔터키로도 검색
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      searchBtn.click();
    }
  });
});
