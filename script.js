document.addEventListener('DOMContentLoaded', () => {
  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');
  const resultsDiv = document.getElementById('results');

  searchBtn.addEventListener('click', () => {
    const query = searchInput.value.trim();
    if (!query) {
      resultsDiv.innerHTML = '<p style="color:red;">검색어를 입력하세요.</p>';
      return;
    }
    // 간단한 더미 결과 생성
    const dummyResults = [
      `${query}에 대한 첫 번째 결과`,
      `${query}에 대한 두 번째 결과`,
      `${query}에 대한 세 번째 결과`
    ];
    resultsDiv.innerHTML = dummyResults.map(item => `<p>• ${item}</p>`).join('');
  });

  // 엔터키로도 검색
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      searchBtn.click();
    }
  });
});
