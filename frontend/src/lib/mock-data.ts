import heroImg from "@/assets/vinwonders-hero.jpg";
import tataImg from "@/assets/tata-show.jpg";
import fountainImg from "@/assets/fountain-show.jpg";
import safariImg from "@/assets/safari.jpg";

export const itinerary = [
  {
    day: 1,
    label: "Thứ Bảy · 7 Tháng 6",
    items: [
      { time: "06:40", title: "Bay VN1827 · Hà Nội → Phú Quốc", location: "Sân bay Nội Bài (HAN)", duration: "2h 15m", icon: "plane" },
      { time: "10:30", title: "Nhận phòng Vinpearl Resort", location: "Bãi Dài, Phú Quốc", duration: "30m", icon: "hotel" },
      { time: "13:00", title: "Vinpearl Safari · Vườn thú bán hoang dã", location: "Vinpearl Safari Phú Quốc", duration: "3h", icon: "safari" },
      { time: "19:30", title: "Tata Show · Show diễn nghệ thuật đa giác quan", location: "Grand World, Phú Quốc", duration: "75 phút", icon: "show" },
    ],
  },
  {
    day: 2,
    label: "Chủ Nhật · 8 Tháng 6",
    items: [
      { time: "09:00", title: "VinWonders Phú Quốc · Công viên chủ đề", location: "Bãi Dài", duration: "Cả ngày", icon: "park" },
      { time: "18:45", title: "Show Nhạc Nước · Symphony of the Sea", location: "Sun Set Town", duration: "20 phút", icon: "fountain" },
      { time: "21:30", title: "Bay VN1828 · Phú Quốc → Hà Nội", location: "Sân bay Phú Quốc (PQC)", duration: "2h 10m", icon: "plane" },
    ],
  },
];

export const flights = [
  {
    id: "VN1827",
    airline: "Vietnam Airlines",
    code: "VN 1827",
    from: { city: "Hà Nội", code: "HAN", time: "06:40" },
    to: { city: "Phú Quốc", code: "PQC", time: "08:55" },
    date: "Thứ Bảy, 07/06",
    duration: "2h 15m",
    stops: "Bay thẳng",
    price: 1890000,
  },
  {
    id: "VN1828",
    airline: "Vietnam Airlines",
    code: "VN 1828",
    from: { city: "Phú Quốc", code: "PQC", time: "21:30" },
    to: { city: "Hà Nội", code: "HAN", time: "23:40" },
    date: "Chủ Nhật, 08/06",
    duration: "2h 10m",
    stops: "Bay thẳng",
    price: 1740000,
  },
];

export const tickets = [
  {
    id: "vw-combo",
    title: "VinWonders + Safari Combo 2 ngày",
    subtitle: "Vé vào cổng không giới hạn · Buffet trưa",
    price: 1150000,
    original: 1450000,
    badge: "Giảm 20%",
    image: heroImg,
  },
  {
    id: "tata",
    title: "Tata Show · Hạng VIP",
    subtitle: "Ghế trung tâm · Welcome drink",
    price: 850000,
    original: 1050000,
    badge: "Hot",
    image: tataImg,
  },
];

export const events = [
  {
    id: "tata",
    title: "Tata Show",
    venue: "Grand World Phú Quốc",
    image: tataImg,
    status: "live",
    countdown: "Bắt đầu sau 20 phút",
    rating: 4.9,
  },
  {
    id: "fountain",
    title: "Symphony of the Sea",
    venue: "Sun Set Town",
    image: fountainImg,
    status: "soon",
    countdown: "Hôm nay · 18:45",
    rating: 4.8,
  },
  {
    id: "safari",
    title: "Vinpearl Safari Night",
    venue: "Vinpearl Safari",
    image: safariImg,
    status: "scheduled",
    countdown: "Mai · 19:00",
    rating: 4.7,
  },
];

export const reasoningSteps = [
  "Phân tích yêu cầu: chuyến đi cuối tuần HAN → PQC",
  "Kiểm tra chuyến bay Vietnam Airlines & Vietjet",
  "Tra cứu vé VinWonders + Safari combo",
  "Đối chiếu lịch show: Tata Show, Nhạc nước",
  "Tối ưu lịch trình 2 ngày 1 đêm",
];

export const formatVND = (n: number) =>
  new Intl.NumberFormat("vi-VN").format(n) + "₫";
