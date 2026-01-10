import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type Timeframe = "1m" | "5m" | "15m" | "30m" | "1h" | "4h" | "1D" | "1W" | "1M";

interface TimeframeSelectorProps {
  selected: Timeframe;
  onSelect: (timeframe: Timeframe) => void;
}

const timeframes: { value: Timeframe; label: string }[] = [
  { value: "1m", label: "1m" },
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
  { value: "30m", label: "30m" },
  { value: "1h", label: "1H" },
  { value: "4h", label: "4H" },
  { value: "1D", label: "1D" },
  { value: "1W", label: "1W" },
  { value: "1M", label: "1M" },
];

export function TimeframeSelector({ selected, onSelect }: TimeframeSelectorProps) {
  return (
    <div className="flex items-center gap-1 p-1 rounded-lg bg-secondary/50">
      {timeframes.map((tf) => (
        <Button
          key={tf.value}
          variant="ghost"
          size="sm"
          className={cn(
            "h-7 px-2 text-xs font-mono",
            selected === tf.value && "bg-primary text-primary-foreground hover:bg-primary/90"
          )}
          onClick={() => onSelect(tf.value)}
        >
          {tf.label}
        </Button>
      ))}
    </div>
  );
}
