"""Dynamic (runtime) AI message translations.

The static i18n LANG dict covers labels; this translates the live sentences
produced by the watcher, grid instructions, and briefings so the running app
speaks the user's language. Falls back to English.
"""
from __future__ import annotations

# Key -> per-language sentence. {n} placeholders filled with .format().
M = {
    # watcher / instructions
    "grid_running": {
        "en": "Running the buy-low / sell-high grid.",
        "th": "กำลังทำงานกริดซื้อถูก–ขายสูง",
        "zh": "正在运行低买高卖网格。",
        "vi": "Đang chạy lưới mua thấp / bán cao.",
        "es": "Grids en marcha: comprar bajo, vender alto.",
    },
    "buy_zone": {
        "en": "BELOW range — bargain / buy-low zone.",
        "th": "ต่ำกว่าช่วง — โซนซื้อ (ราคาถูก)",
        "zh": "低于区间 — 抄底买入区。",
        "vi": "Dưới vùng — vùng mua rẻ.",
        "es": "Por debajo del rango — zona de compra baja.",
    },
    "sell_zone": {
        "en": "ABOVE range — sell-high zone.",
        "th": "สูงกว่าช่วง — โซนขายทำกำไร",
        "zh": "高于区间 — 高卖区。",
        "vi": "Trên vùng — vùng bán cao.",
        "es": "Por encima del rango — zona de venta alta.",
    },
    "pause_down": {
        "en": "PAUSE buying — strong downtrend. Protecting capital.",
        "th": "หยุดซื้อชั่วคราว — ตลาดลงแรง กำลังปกป้องเงินต้น",
        "zh": "暂停买入 — 强劲下跌趋势，正在保护资金。",
        "vi": "TẠM DỪNG mua — xu hướng giảm mạnh, đang bảo vệ vốn.",
        "es": "PAUSA en compras — fuerte tendencia bajista. Protegiendo capital.",
    },
    "pause_up": {
        "en": "PAUSE buying — price above grid; let lows sell into strength.",
        "th": "หยุดซื้อ — ราคาสูงกว่ากริด ปล่อยให้ของเดิมขายทำกำไร",
        "zh": "暂停买入 — 价格高于网格；让低位筹码顺势卖出。",
        "vi": "TẠM DỪNG mua — giá trên lưới; để lệnh cũ bán theo đà tăng.",
        "es": "PAUSA en compras — precio sobre el grid; que las ventas aprovechen la fuerza.",
    },
    "profit_locked": {
        "en": "Trailing exit locked — profit banked. Sell high ✔",
        "th": "ล็อกกำไรแล้ว — ขายทำกำไรเรียบร้อย ✔",
        "zh": "移动止盈已锁定 — 利润已落袋 ✔",
        "vi": "Chốt lãi theo giá — đã ghi nhận lợi nhuận ✔",
        "es": "Salida con trailing activada — beneficio asegurado ✔",
    },
    # actions
    "action_GRID": {"en": "RUN", "th": "ทำงาน", "zh": "运行", "vi": "CHẠY", "es": "ACTIVO"},
    "action_BUY": {"en": "BUY", "th": "ซื้อ", "zh": "买入", "vi": "MUA", "es": "COMPRAR"},
    "action_SELL": {"en": "SELL", "th": "ขาย", "zh": "卖出", "vi": "BÁN", "es": "VENDER"},
    "action_HOLD": {"en": "HOLD", "th": "ถือ/หยุด", "zh": "暂停", "vi": "GIỮ", "es": "ESPERA"},
    "action_BANK_PROFIT": {"en": "PROFIT", "th": "ล็อกกำไร", "zh": "止盈", "vi": "CHỐT LÃI", "es": "BENEFICIO"},
    # watcher states
    "state_BEST_BUY": {"en": "BUY signal", "th": "สัญญาณซื้อ", "zh": "买入信号", "vi": "Tín hiệu MUA", "es": "Señal de compra"},
    "state_BEST_SELL": {"en": "SELL signal", "th": "สัญญาณขาย", "zh": "卖出信号", "vi": "Tín hiệu BÁN", "es": "Señal de venta"},
    "state_PAUSE": {"en": "Paused", "th": "หยุดชั่วคราว", "zh": "已暂停", "vi": "Tạm dừng", "es": "En pausa"},
    "state_BANK": {"en": "Profit locked", "th": "ล็อกกำไร", "zh": "利润锁定", "vi": "Đã chốt lãi", "es": "Beneficio asegurado"},
    "state_GRID": {"en": "Running", "th": "ทำงาน", "zh": "运行中", "vi": "Đang chạy", "es": "Activo"},
    # briefing
    "golden_rule": {
        "en": "Golden rule: BUY LOW, SELL HIGH — buys below price, sells above; pauses in crashes and trails winners to bank profit.",
        "th": "กฎทอง: ซื้อถูก ขายสูง — ซื้อต่ำกว่าราคา ขายสูงกว่า หยุดในตลาดพัง และเลื่อนจุดขายล็อกกำไร",
        "zh": "黄金法则：低买高卖 — 价格下方挂买、上方挂卖；崩盘暂停，移动止盈锁定利润。",
        "vi": "Quy tắc vàng: MUA THẤP BÁN CAO — mua dưới giá, bán trên giá; tạm dừng khi sập và trailing chốt lãi.",
        "es": "Regla de oro: COMPRAR BAJO, VENDER ALTO — compras bajo el precio, ventas por encima; pausa en caídas y trailing para asegurar beneficios.",
    },
    "overall_in_profit": {
        "en": "Your {n} grid(s) are doing well overall, total P/L {pnl} across {rt} buy→sell cycles.",
        "th": "กริด {n} ตัวโดยรวมกำไร รวม {pnl} จาก {rt} รอบซื้อ→ขาย",
        "zh": "您的 {n} 个网格总体表现良好，{rt} 个买卖周期，总盈亏 {pnl}。",
        "vi": "Tổng thể {n} lưới đang tốt, lãi/lỗ {pnl} qua {rt} chu kỳ mua→bán.",
        "es": "Tus {n} grids van bien en total, P/L {pnl} en {rt} ciclos compra→venta.",
    },
    "overall_flat": {
        "en": "Your {n} grid(s) are roughly flat, total P/L {pnl} across {rt} cycles.",
        "th": "กริด {n} ตัวโดยรวมทรงตัว รวม {pnl} จาก {rt} รอบ",
        "zh": "您的 {n} 个网格基本持平，{rt} 个周期，总盈亏 {pnl}。",
        "vi": "{n} lưới nhìn chung đi ngang, P/L {pnl} qua {rt} chu kỳ.",
        "es": "Tus {n} grids están planos, P/L {pnl} en {rt} ciclos.",
    },
    "overall_down": {
        "en": "Your {n} grid(s) are in a drawdown — safety limits are working. Total {pnl}.",
        "th": "กริด {n} ตัวกำลังขาดทุน — ระบบความปลอดภัยทำงาน รวม {pnl}",
        "zh": "您的 {n} 个网格处于回撤 — 安全限制正在生效。总计 {pnl}。",
        "vi": "{n} lưới đang bị rút vốn — giới hạn an toàn đang hoạt động. Tổng {pnl}.",
        "es": "Tus {n} grids están en drawdown — los límites de seguridad funcionan. Total {pnl}.",
    },
    "protection_active": {
        "en": "Protection is active on: {coins}. Grids resume when the market returns to a range.",
        "th": "กำลังปกป้อง: {coins} จะกลับมาทำงานเมื่อตลาดกลับเข้าสู่กรอบ",
        "zh": "保护已开启：{coins}。市场回到区间时网格自动恢复。",
        "vi": "Bảo vệ đang bật: {coins}. Lưới chạy lại khi thị trường về vùng.",
        "es": "Protección activa en: {coins}. Los grids se reanudan al volver el rango.",
    },
    "all_normal": {
        "en": "All active grids are running normally within their ranges.",
        "th": "กริดที่ทำงานทั้งหมดเป็นปกติในกรอบราคา",
        "zh": "所有运行中的网格在区间内正常工作。",
        "vi": "Tất cả lưới đang chạy bình thường trong vùng giá.",
        "es": "Todos los grids activos funcionan normalmente en su rango.",
    },
    "no_grids": {
        "en": "No grids running right now. Start a practice grid to watch the AI work.",
        "th": "ยังไม่มีกริดทำงาน ลองเริ่มกริดฝึกเพื่อดู AI ทำงาน",
        "zh": "当前没有运行中的网格。启动一个练习网格观看 AI 工作。",
        "vi": "Chưa có lưới nào chạy. Hãy bắt đầu một lưới thực tập để xem AI hoạt động.",
        "es": "No hay grids activos. Inicia un grid de práctica para ver trabajar a la IA.",
    },
    "best_buy_now": {
        "en": "Best BUY now: {coin} at {price} (buy low).",
        "th": "จังหวะซื้อดีสุด: {coin} ที่ {price} (ซื้อถูก)",
        "zh": "现在最佳买入：{coin} @ {price}（低买）。",
        "vi": "Nên MUA lúc này: {coin} giá {price} (mua thấp).",
        "es": "Mejor COMPRA ahora: {coin} a {price} (comprar bajo).",
    },
    "best_sell_now": {
        "en": "Best SELL now: {coin} at {price} (take profit).",
        "th": "จังหวะขายดีสุด: {coin} ที่ {price} (ขายทำกำไร)",
        "zh": "现在最佳卖出：{coin} @ {price}（止盈）。",
        "vi": "Nên BÁN lúc này: {coin} giá {price} (chốt lời).",
        "es": "Mejor VENTA ahora: {coin} a {price} (tomar beneficio).",
    },
    "paused_list": {
        "en": "Paused (crash protection): {coins}",
        "th": "หยุด (ป้องกันตลาดพัง): {coins}",
        "zh": "已暂停（崩盘保护）：{coins}",
        "vi": "Tạm dừng (bảo vệ sập giá): {coins}",
        "es": "En pausa (protección): {coins}",
    },
    "no_standout": {
        "en": "No standout moment — grids are running their buy-low/sell-high cycles.",
        "th": "ยังไม่มีจังหวะเด่น — กริดกำลังทำงานรอบซื้อถูกขายสูง",
        "zh": "暂无突出时机 — 网格正在执行低买高卖循环。",
        "vi": "Chưa có thời điểm nổi bật — lưới đang chạy chu kỳ mua thấp/bán cao.",
        "es": "Sin momento destacado — los grids ejecutan sus ciclos de compra baja/venta alta.",
    },
    "next_buy_sell": {
        "en": "next BUY LOW ~ {buy} · next SELL HIGH ~ {sell}",
        "th": "ซื้อต่ำ ~ {buy} · ขายสูง ~ {sell}",
        "zh": "下次低买 ~ {buy} · 高卖 ~ {sell}",
        "vi": "MUA thấp ~ {buy} · BÁN cao ~ {sell}",
        "es": "próxima COMPRA ~ {buy} · próxima VENTA ~ {sell}",
    },
}


def msg(key: str, lang: str = "en", **kw) -> str:
    lang = lang if lang in ("en", "th", "zh", "vi", "es") else "en"
    entry = M.get(key, {}).get(lang)
    if entry is None:
        entry = M.get(key, {}).get("en", key)
    try:
        return entry.format(**kw)
    except Exception:
        return entry
