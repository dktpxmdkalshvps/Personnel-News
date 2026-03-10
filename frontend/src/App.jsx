import { useState, useEffect, useCallback } from "react";
import NewsCard from "./components/NewsCard";
import FilterBar from "./components/FilterBar";
import StatsPanel from "./components/StatsPanel";
import NewsModal from "./components/NewsModal";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [news, setNews] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [selectedItem, setSelectedItem] = useState(null);

  const [filters, setFilters] = useState({
    source: "",
    category: "",
  });

  const LIMIT = 30;

  const fetchNews = useCallback(
    async (newOffset = 0) => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          limit: LIMIT,
          offset: newOffset,
          ...(filters.source && { source: filters.source }),
          ...(filters.category && { category: filters.category }),
        });
        const res = await fetch(`${API_BASE}/api/news?${params}`);
        if (!res.ok) throw new Error("서버 오류");
        const data = await res.json();
        if (newOffset === 0) {
          setNews(data.items);
        } else {
          setNews((prev) => [...prev, ...data.items]);
        }
        setTotal(data.total);
        setOffset(newOffset);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    },
    [filters]
  );

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stats`);
      const data = await res.json();
      setStats(data);
    } catch {}
  }, []);

  useEffect(() => {
    setOffset(0);
    fetchNews(0);
    fetchStats();
  }, [filters, fetchNews, fetchStats]);

  const handleLoadMore = () => fetchNews(offset + LIMIT);

  const handleCrawl = async () => {
    if (!confirm("수동으로 크롤링을 실행할까요?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/crawl`, { method: "POST" });
      const data = await res.json();
      alert(data.message);
      fetchNews(0);
      fetchStats();
    } catch {
      alert("크롤링 실패");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📋</span>
            <div>
              <h1 className="text-lg font-bold text-gray-900">인사·동정·부고 뉴스</h1>
              <p className="text-xs text-gray-500">연합뉴스 · 한국경제 자동 수집</p>
            </div>
          </div>
          <button
            onClick={handleCrawl}
            className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            🔄 수동 수집
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* 통계 */}
        {stats && <StatsPanel stats={stats} />}

        {/* 필터 */}
        <FilterBar filters={filters} onChange={setFilters} total={total} />

        {/* 에러 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
            ⚠️ {error} — API 서버가 실행 중인지 확인하세요.
          </div>
        )}

        {/* 뉴스 그리드 */}
        {loading && news.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(9)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl p-4 animate-pulse">
                <div className="h-3 bg-gray-200 rounded w-1/3 mb-3" />
                <div className="h-5 bg-gray-200 rounded w-full mb-2" />
                <div className="h-4 bg-gray-200 rounded w-3/4" />
              </div>
            ))}
          </div>
        ) : news.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <p className="text-4xl mb-3">📭</p>
            <p>수집된 뉴스가 없습니다.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {news.map((item) => (
              <NewsCard key={item.id} item={item} onClick={() => setSelectedItem(item)} />
            ))}
          </div>
        )}

        {/* 더 보기 */}
        {news.length < total && (
          <div className="flex justify-center">
            <button
              onClick={handleLoadMore}
              disabled={loading}
              className="px-6 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition"
            >
              {loading ? "로딩 중…" : `더 보기 (${total - news.length}건 남음)`}
            </button>
          </div>
        )}
      </div>

      {/* 상세 모달 */}
      {selectedItem && (
        <NewsModal item={selectedItem} onClose={() => setSelectedItem(null)} />
      )}
    </div>
  );
}

export default App;
