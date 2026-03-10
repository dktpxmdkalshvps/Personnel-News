const SOURCE_LABEL = { yna: "연합뉴스", hankyung: "한국경제" };
const SOURCE_COLOR = { yna: "bg-blue-100 text-blue-700", hankyung: "bg-amber-100 text-amber-700" };
const CATEGORY_EMOJI = { 인사: "🏢", 동정: "🤝", 부고: "🕯️" };
const CATEGORY_COLOR = {
  인사: "bg-green-100 text-green-700",
  동정: "bg-purple-100 text-purple-700",
  부고: "bg-gray-200 text-gray-600",
};

function formatDate(dt) {
  if (!dt) return "";
  const d = new Date(dt);
  if (isNaN(d)) return "";
  return d.toLocaleString("ko-KR", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function NewsCard({ item, onClick }) {
  const preview = (item.content || "").replace(/\n+/g, " ").slice(0, 120);

  const handleShare = async (e) => {
    e.stopPropagation();
    if (navigator.share) {
      await navigator.share({ title: item.title, url: item.url });
    } else {
      await navigator.clipboard.writeText(item.url);
      alert("링크가 복사되었습니다.");
    }
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 cursor-pointer hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex flex-col gap-3"
    >
      {/* 배지 */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${CATEGORY_COLOR[item.category] || "bg-gray-100 text-gray-600"}`}>
          {CATEGORY_EMOJI[item.category] || "📋"} {item.category}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded-full ${SOURCE_COLOR[item.source] || "bg-gray-100 text-gray-500"}`}>
          {SOURCE_LABEL[item.source] || item.source}
        </span>
      </div>

      {/* 제목 */}
      <h3 className="font-semibold text-gray-900 text-sm leading-snug line-clamp-2">
        {item.title}
      </h3>

      {/* 미리보기 */}
      {preview && (
        <p className="text-xs text-gray-500 leading-relaxed line-clamp-3">{preview}</p>
      )}

      {/* 하단 */}
      <div className="flex items-center justify-between mt-auto pt-2 border-t border-gray-50">
        <span className="text-xs text-gray-400">{formatDate(item.published_at)}</span>
        <div className="flex gap-2">
          <button
            onClick={handleShare}
            className="text-xs text-gray-400 hover:text-blue-600 transition"
            title="공유"
          >
            🔗
          </button>
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-xs text-gray-400 hover:text-blue-600 transition"
            title="원문"
          >
            ↗
          </a>
        </div>
      </div>
    </div>
  );
}
