"""Tiny dependency-free i18n.

Languages supported for the UI and the AI's plain-language summaries.
Detection priority: saved config -> OLLAMA/browser default -> English.
All translations live in LANG (UI keys) and t() does a fallback to English.
"""
from __future__ import annotations

LANGUAGES = [
    ("en", "English"),
    ("th", "ไทย (Thai)"),
    ("zh", "中文 (Chinese)"),
    ("vi", "Tiếng Việt (Vietnamese)"),
    ("es", "Español (Spanish)"),
]

# Core UI labels. Keep keys short; fall back to English when missing.
LANG = {
    "en": {
        "app_name": "Super AI Trader",
        "safety_on": "Safety Shield ON — your keys stay on your computer, money cannot be withdrawn",
        "practice": "PRACTICE (safe)",
        "connect": "CONNECT EXCHANGE",
        "tell_ai": "Tell your AI what you want",
        "live_market": "Live market",
        "multi_grids": "Multi-coin grids (practice money)",
        "start_grids": "Start grids",
        "stop_all": "Stop all grids (safe)",
        "today_pl": "Today P/L",
        "total_pl": "Total P/L",
        "grids_running": "Grids running",
        "running": "Running",
        "paused": "Paused",
        "buys": "buys",
        "sells": "sells",
        "emergency": "EMERGENCY STOP — cancel ALL orders",
        "test_connection": "Test connection",
        "enlarge_chart": "Enlarge chart",
        "replay": "Time Machine — replay real past candles",
        "quick_demo": "Start a quick demo (practice)",
        "close": "Close",
    },
    "th": {
        "app_name": "Super AI Trader",
        "safety_on": "เปิดระบบความปลอดภัย — คีย์ของคุณอยู่ในเครื่องนี้เท่านั้น ถอนเงินไม่ได้",
        "practice": "โหมดฝึก (ปลอดภัย)",
        "connect": "เชื่อมต่อตลาด (Binance / Gate)",
        "tell_ai": "บอก AI ว่าคุณต้องการอะไร",
        "live_market": "ตลาดสด",
        "multi_grids": "กริดหลายเหรียญ (เงินจำลอง)",
        "start_grids": "เริ่มกริด",
        "stop_all": "หยุดทุกกริดอย่างปลอดภัย",
        "today_pl": "กำไรวันนี้",
        "total_pl": "กำไรรวม",
        "grids_running": "กริดที่ทำงาน",
        "running": "ทำงาน",
        "paused": "หยุดชั่วคราว",
        "buys": "ซื้อ",
        "sells": "ขาย",
        "emergency": "หยุดฉุกเฉิน — ยกเลิกคำสั่งทั้งหมด",
        "test_connection": "ทดสอบการเชื่อมต่อ",
        "enlarge_chart": "ขยายกราฟ",
        "replay": "ไทม์แมชีน — ย้อนดูแท่งเทียนจริง",
        "quick_demo": "เริ่มตัวอย่างด่วน (โหมดฝึก)",
        "close": "ปิด",
    },
    "zh": {
        "app_name": "Super AI Trader",
        "safety_on": "安全护盾已开启 — 密钥仅在本机，无法提币",
        "practice": "练习模式（安全）",
        "connect": "连接交易所",
        "tell_ai": "告诉 AI 你想要什么",
        "live_market": "实时行情",
        "multi_grids": "多币网格（模拟资金）",
        "start_grids": "启动网格",
        "stop_all": "安全停止全部网格",
        "today_pl": "今日盈亏",
        "total_pl": "总盈亏",
        "grids_running": "运行中的网格",
        "running": "运行中",
        "paused": "已暂停",
        "buys": "买入",
        "sells": "卖出",
        "emergency": "紧急停止 — 撤销所有订单",
        "test_connection": "测试连接",
        "enlarge_chart": "放大图表",
        "replay": "时光机 — 回放历史K线",
        "quick_demo": "快速演示（练习）",
        "close": "关闭",
    },
    "vi": {
        "app_name": "Super AI Trader",
        "safety_on": "Lá chắn an toàn BẬT — khóa nằm trên máy này, không thể rút tiền",
        "practice": "THỰC TẬP (an toàn)",
        "connect": "KẾT NỐI SÀN",
        "tell_ai": "Nói cho AI biết bạn muốn gì",
        "live_market": "Thị trường trực tiếp",
        "multi_grids": "Lưới nhiều coin (tiền ảo)",
        "start_grids": "Bắt đầu lưới",
        "stop_all": "Dừng toàn bộ lưới (an toàn)",
        "today_pl": "Lãi hôm nay",
        "total_pl": "Tổng lãi/lỗ",
        "grids_running": "Lưới đang chạy",
        "running": "Đang chạy",
        "paused": "Tạm dừng",
        "buys": "mua",
        "sells": "bán",
        "emergency": "DỪNG KHẨN CẤP — hủy mọi lệnh",
        "test_connection": "Kiểm tra kết nối",
        "enlarge_chart": "Phóng to biểu đồ",
        "replay": "Cỗ máy thời gian — xem lại nến thật",
        "quick_demo": "Bắt đầu demo nhanh (thực tập)",
        "close": "Đóng",
    },
    "es": {
        "app_name": "Super AI Trader",
        "safety_on": "Escudo de seguridad activado — tus claves quedan en este equipo, no se puede retirar",
        "practice": "PRÁCTICA (seguro)",
        "connect": "CONECTAR EXCHANGE",
        "tell_ai": "Dile a tu AI qué quieres",
        "live_market": "Mercado en vivo",
        "multi_grids": "Grids multi-coin (dinero de práctica)",
        "start_grids": "Iniciar grids",
        "stop_all": "Detener todos los grids (seguro)",
        "today_pl": "P/L de hoy",
        "total_pl": "P/L total",
        "grids_running": "Grids activos",
        "running": "Activo",
        "paused": "Pausado",
        "buys": "compras",
        "sells": "ventas",
        "emergency": "PARADA DE EMERGENCIA — cancelar TODAS las órdenes",
        "test_connection": "Probar conexión",
        "enlarge_chart": "Ampliar gráfico",
        "replay": "Máquina del tiempo — repetir velas reales",
        "quick_demo": "Iniciar demo rápida (práctica)",
        "close": "Cerrar",
    },
}


def supported() -> list:
    return LANGUAGES


def t(key: str, lang: str = "en") -> str:
    """Translate a key; fall back to English, then the key itself."""
    lang = lang if lang in LANG else "en"
    return LANG.get(lang, {}).get(key, LANG["en"].get(key, key))
