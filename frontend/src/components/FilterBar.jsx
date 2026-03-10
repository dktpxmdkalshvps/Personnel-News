export default function FilterBar({ filters, onChange, total }) {
  const categories = ["", "인사", "동정", "부고"];
  const sources = [
    { value: "", label: "전체 소스" },
    { value: "yna", label: "연합뉴스" },
    { value: "hankyung", label: "한국경제" },
  ];

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* 카테고리 탭 */}
      <div className="flex gap-1 bg-white border border-gray-200 rounded-lg p-1">
        {categories.map((cat) => (
          <button
            key={cat || "all"}
            onClick={() => onChange((f) => ({ ...f, category: cat }))}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
              filters.category === cat
                ? "bg-blue-600 text-white shadow-sm"
                : "text-gray-600 hover:bg-gray-50"
            }`}
          >
            {cat === "" ? "전체" : cat === "인사" ? "🏢 인사" : cat === "동정" ? "🤝 동정" : "🕯️ 부고"}
          </button>
        ))}
      </div>

      {/* 소스 선택 */}
      <select
        value={filters.source}
        onChange={(e) => onChange((f) => ({ ...f, source: e.target.value }))}
        className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {sources.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>

      {/* 총 건수 */}
      <span className="ml-auto text-sm text-gray-400">총 {total.toLocaleString()}건</span>
    </div>
  );
}
