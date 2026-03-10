import { useEffect } from "react";

const SOURCE_LABEL = { yna: "연합뉴스", hankyung: "한국경제" };
const CATEGORY_EMOJI = { 인사: "🏢", 동정: "🤝", 부고: "🕯️" };

function formatDate(dt) {
  if (!dt) return "";
  const d = new Date(dt);
  return isNaN(d) ? "" : d.toLocaleString("ko-KR");
}

export default function NewsModal({ item, onClose }) {
  // ESC 키로 닫기
  useEffect(() => {
    const handler = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleShare = async () => {
    const text = `${item.title}\n${item.url}`;
    if (navigator.share) {
      await navigator.share({ title: item.title, text, url: item.url });
    } else {
      await navigator.clipboard.writeText(text);
      alert("제목과 링크가 복사되었습니다.");
    }
  };

  // 본문 줄바꿈 처리
  const contentLines = (item.content || "").split("\n").filter(Boolean);

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="p-5 border-b border-gray-100 flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="text-sm font-semibold text-gray-600">
                {CATEGORY_EMOJI[item.category]} {item.category}
              </span>
              <span className="text-sm text-gray-400">|</span>
              <span className="text-sm text-gray-500">{SOURCE_LABEL[item.source] || item.source}</span>
              {item.published_at && (
                <>
                  <span className="text-sm text-gray-400">|</span>
                  <span className="text-sm text-gray-400">{formatDate(item.published_at)}</span>
                </>
              )}
            </div>
            <h2 className="text-lg font-bold text-gray-900 leading-snug">{item.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl flex-shrink-0 mt-0.5"
          >
            ✕
          </button>
        </div>

        {/* 본문 */}
        <div className="p-5 overflow-y-auto flex-1">
          {contentLines.length > 0 ? (
            <div className="space-y-1.5">
              {contentLines.map((line, i) => (
                <p key={i} className="text-sm text-gray-700 leading-relaxed">
                  {line}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-10">본문이 없습니다.</p>
          )}
        </div>

        {/* 하단 버튼 */}
        <div className="p-4 border-t border-gray-100 flex items-center gap-3">
          <button
            onClick={handleShare}
            className="flex-1 py-2 text-sm font-medium border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition"
          >
            🔗 공유하기
          </button>
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg text-center hover:bg-blue-700 transition"
          >
            원문 보기 ↗
          </a>
        </div>
      </div>
    </div>
  );
}
