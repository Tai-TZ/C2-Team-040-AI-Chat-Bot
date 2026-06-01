import { CloudRain, CloudSun, Droplets, Thermometer, Wind } from "lucide-react";
import type { WeatherInfo } from "@/lib/dashboard-context";

const ICON_BASE = "https://openweathermap.org/img/wn";

type Props = {
  weather: WeatherInfo;
  compact?: boolean;
};

export function WeatherCard({ weather, compact = false }: Props) {
  const rainy = weather.hasRain || weather.rainRisk === "high";
  const iconUrl = weather.icon ? `${ICON_BASE}/${weather.icon}@2x.png` : null;

  return (
    <div
      className={`rounded-2xl border shadow-soft overflow-hidden ${
        rainy
          ? "border-sky-300/50 bg-gradient-to-br from-sky-50 to-slate-100 dark:from-sky-950/40 dark:to-slate-900"
          : "border-amber-200/50 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/20"
      }`}
    >
      <div className="flex items-start justify-between gap-3 p-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Thời tiết · {weather.usingDate}
          </p>
          <h3 className="mt-1 text-lg font-bold text-foreground">
            {weather.location}
          </h3>
          <p className="mt-0.5 capitalize text-sm text-muted-foreground">
            {weather.description}
          </p>
        </div>
        {iconUrl ? (
          <img
            src={iconUrl}
            alt=""
            className="h-16 w-16 shrink-0"
            width={64}
            height={64}
          />
        ) : rainy ? (
          <CloudRain className="h-12 w-12 shrink-0 text-sky-600" />
        ) : (
          <CloudSun className="h-12 w-12 shrink-0 text-amber-500" />
        )}
      </div>

      <div
        className={`grid gap-2 px-4 pb-4 ${compact ? "grid-cols-2" : "grid-cols-2 sm:grid-cols-4"}`}
      >
        {weather.tempC != null && (
          <Stat
            icon={Thermometer}
            label="Nhiệt độ"
            value={`${weather.tempC}°C`}
          />
        )}
        {weather.feelsLikeC != null && !compact && (
          <Stat
            icon={Thermometer}
            label="Cảm giác"
            value={`${weather.feelsLikeC}°C`}
          />
        )}
        {weather.humidity != null && (
          <Stat icon={Droplets} label="Độ ẩm" value={`${weather.humidity}%`} />
        )}
        {weather.popPercent != null && (
          <Stat icon={CloudRain} label="Khả năng mưa" value={`${weather.popPercent}%`} />
        )}
        {weather.windMs != null && !compact && (
          <Stat icon={Wind} label="Gió" value={`${weather.windMs} m/s`} />
        )}
      </div>

      {weather.recommendation && (
        <div
          className={`mx-4 mb-4 rounded-xl px-3 py-2.5 text-xs leading-relaxed ${
            rainy
              ? "bg-sky-100/80 text-sky-900 dark:bg-sky-900/40 dark:text-sky-100"
              : "bg-amber-100/80 text-amber-900 dark:bg-amber-900/30 dark:text-amber-100"
          }`}
        >
          {weather.recommendation}
        </div>
      )}
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Thermometer;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-background/70 px-2.5 py-2">
      <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
        <Icon className="h-3 w-3" />
        {label}
      </div>
      <p className="mt-0.5 text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}
