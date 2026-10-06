export type ParamField = { key: string; label: string; kind?: "bool"; min?: number; max?: number; integer?: boolean; percent?: boolean };
export const PARAM_GROUPS: { title: string; description: string; fields: ParamField[] }[] = [
  { title: "基本面門檻", description: "設定企業獲利品質的篩選條件。", fields: [
    { key: "eps_threshold", label: "EPS 最小門檻" }, { key: "roe_threshold", label: "ROE 最小門檻 (%)" }, { key: "fundamental_pass_required", label: "基本面通過才可 BUY", kind: "bool" },
  ] },
  { title: "回測與訊號", description: "回測期間與持有天數會影響分析時間。", fields: [
    { key: "backtest_years", label: "回測年數", min: 1, max: 10, integer: true }, { key: "hold_days", label: "持有天數", min: 1, max: 120, integer: true }, { key: "min_tech_score_for_signal", label: "回測技術分門檻", min: 0, max: 100, integer: true },
  ] },
  { title: "風險設定", description: "以百分比輸入；例如 10 表示 10%。", fields: [
    { key: "target_return", label: "停利目標 (%)", min: 1, max: 50, percent: true }, { key: "stop_loss", label: "停損幅度 (%)", min: 1, max: 50, percent: true },
  ] },
  { title: "評分加權", description: "三項權重需合計 100%。", fields: [
    { key: "weight_fundamental", label: "基本面權重 (%)", min: 0, max: 100, percent: true }, { key: "weight_technical", label: "技術面權重 (%)", min: 0, max: 100, percent: true }, { key: "weight_backtest", label: "回測權重 (%)", min: 0, max: 100, percent: true },
    { key: "min_total_score_for_buy", label: "BUY 綜合分門檻", min: 0, max: 100, integer: true }, { key: "min_tech_score_for_buy", label: "BUY 技術分門檻", min: 0, max: 100, integer: true },
  ] },
  { title: "技術訊號", description: "啟用要納入評分的技術指標。", fields: [
    { key: "use_ma_alignment", label: "均線多頭排列", kind: "bool" }, { key: "use_bollinger_bounce", label: "布林下軌反彈", kind: "bool" }, { key: "use_kd_golden_cross", label: "KD 黃金交叉", kind: "bool" }, { key: "use_macd_bullish", label: "MACD 多頭", kind: "bool" }, { key: "use_volume_patterns", label: "量價型態加減分", kind: "bool" },
  ] },
  { title: "大盤濾鏡", description: "大盤跌破指定均線時，將 BUY 降為 WATCH。", fields: [
    { key: "market_filter_enabled", label: "啟用大盤濾鏡", kind: "bool" }, { key: "market_filter_ma_period", label: "濾鏡均線天數", min: 5, max: 120, integer: true },
  ] },
];
export function paramLabel(key: string) { return PARAM_GROUPS.flatMap(group => group.fields).find(field => field.key === key)?.label || key; }
