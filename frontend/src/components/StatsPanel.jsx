const cards = [
  { key: "total", label: "전체", emoji: "📊", color: "bg-blue-50 border-blue-100 text-blue-700" },
  { key: "인사", label: "인사", emoji: "🏢", color: "bg-green-50 border-green-100 text-green-700", sub: "by_category" },
  { key: "동정", label: "동정", emoji: "🤝", color: "bg-purple-50 border-purple-100 text-purple-700", sub: "by_category" },
  { key: "부고", label: "부고", emoji: "🕯️", color: "bg-gray-100 border-gray-200 text-gray-600", sub: "by_category" },
  { key: "yna", label: "연합뉴스", emoji: "📰", color: "bg-sky-50 border-sky-100 text-sky-700", sub: "by_source" },
  { key: "hankyung", label: "한국경제", emoji: "📈", color: "bg-amber-50 border-amber-100 text-amber-700", sub: "by_source" },
];

export default function StatsPanel({ stats }) {
  const getValue = (card) => {
    if (card.sub) return stats[card.sub]?.[card.key] ?? 0;
    return stats[card.key] ?? 0;
  };

  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
      {cards.map((card) => (
        <div key={card.key} className={`rounded-xl border p-3 text-center ${card.color}`}>
          <p className="text-lg">{card.emoji}</p>
          <p className="text-xl font-bold">{getValue(card).toLocaleString()}</p>
          <p className="text-xs mt-0.5 opacity-80">{card.label}</p>
        </div>
      ))}
    </div>
  );
}
