import { useEffect, useRef, useState } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  LineData,
  Time,
  CrosshairMode,
  ColorType,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
} from "lightweight-charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DollarSign, TrendingUp, TrendingDown, MousePointer2 } from "lucide-react";

interface ChartDataPoint {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface IndicatorSeries {
  name: string;
  type: "line" | "histogram";
  data: LineData<Time>[];
  color: string;
  series?: ISeriesApi<"Line"> | ISeriesApi<"Histogram">;
}

interface PLPoint {
  time: Time;
  price: number;
  type: "buy" | "sell";
}

interface InteractiveChartProps {
  data: ChartDataPoint[];
  indicators: IndicatorSeries[];
  symbol: string;
  onPointClick?: (point: PLPoint) => void;
}

export function InteractiveChart({
  data,
  indicators,
  symbol,
  onPointClick,
}: InteractiveChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const indicatorSeriesRef = useRef<(ISeriesApi<"Line"> | ISeriesApi<"Histogram">)[]>([]);
  const [plPoints, setPLPoints] = useState<PLPoint[]>([]);
  const [selectMode, setSelectMode] = useState<"buy" | "sell" | null>(null);
  const [calculatedPL, setCalculatedPL] = useState<{
    profit: number;
    percentage: number;
    buyPrice: number;
    sellPrice: number;
  } | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "hsl(220, 10%, 55%)",
      },
      grid: {
        vertLines: { color: "hsl(220, 15%, 20%)" },
        horzLines: { color: "hsl(220, 15%, 20%)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "hsl(142, 71%, 45%)",
          labelBackgroundColor: "hsl(142, 71%, 45%)",
        },
        horzLine: {
          color: "hsl(142, 71%, 45%)",
          labelBackgroundColor: "hsl(142, 71%, 45%)",
        },
      },
      rightPriceScale: {
        borderColor: "hsl(220, 15%, 20%)",
      },
      timeScale: {
        borderColor: "hsl(220, 15%, 20%)",
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    chartRef.current = chart;

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "hsl(142, 71%, 45%)",
      downColor: "hsl(0, 84%, 60%)",
      borderUpColor: "hsl(142, 71%, 45%)",
      borderDownColor: "hsl(0, 84%, 60%)",
      wickUpColor: "hsl(142, 71%, 45%)",
      wickDownColor: "hsl(0, 84%, 60%)",
    });
    candlestickSeriesRef.current = candlestickSeries;

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "hsl(220, 15%, 35%)",
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "",
    });
    volumeSeriesRef.current = volumeSeries;
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: 500,
        });
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || !data.length) return;

    const candleData: CandlestickData<Time>[] = data.map((d) => ({
      time: d.time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    const volumeData = data.map((d) => ({
      time: d.time,
      value: d.volume,
      color: d.close >= d.open ? "rgba(76, 175, 80, 0.5)" : "rgba(255, 82, 82, 0.5)",
    }));

    candlestickSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);
  }, [data]);

  useEffect(() => {
    if (!chartRef.current) return;

    // Remove old indicator series
    indicatorSeriesRef.current.forEach((series) => {
      try {
        chartRef.current?.removeSeries(series);
      } catch (e) {
        // Series may already be removed
      }
    });
    indicatorSeriesRef.current = [];

    // Add new indicator series
    indicators.forEach((indicator) => {
      if (indicator.type === "line") {
        const series = chartRef.current!.addSeries(LineSeries, {
          color: indicator.color,
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        series.setData(indicator.data);
        indicatorSeriesRef.current.push(series);
      }
    });
  }, [indicators]);

  useEffect(() => {
    if (!chartRef.current || !selectMode) return;

    const handleClick = (param: { time?: Time; point?: { x: number; y: number } }) => {
      if (!param.time || !candlestickSeriesRef.current) return;

      const dataPoint = data.find((d) => d.time === param.time);
      if (!dataPoint) return;

      const newPoint: PLPoint = {
        time: param.time,
        price: dataPoint.close,
        type: selectMode,
      };

      setPLPoints((prev) => {
        const filtered = prev.filter((p) => p.type !== selectMode);
        return [...filtered, newPoint];
      });

      if (onPointClick) {
        onPointClick(newPoint);
      }

      setSelectMode(null);
    };

    chartRef.current.subscribeClick(handleClick);

    return () => {
      chartRef.current?.unsubscribeClick(handleClick);
    };
  }, [selectMode, data, onPointClick]);

  useEffect(() => {
    if (plPoints.length === 2) {
      const buyPoint = plPoints.find((p) => p.type === "buy");
      const sellPoint = plPoints.find((p) => p.type === "sell");

      if (buyPoint && sellPoint) {
        const profit = sellPoint.price - buyPoint.price;
        const percentage = (profit / buyPoint.price) * 100;

        setCalculatedPL({
          profit,
          percentage,
          buyPrice: buyPoint.price,
          sellPrice: sellPoint.price,
        });
      }
    } else {
      setCalculatedPL(null);
    }
  }, [plPoints]);

  const clearPLPoints = () => {
    setPLPoints([]);
    setCalculatedPL(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-primary">
            {symbol}
          </Badge>
          {indicators.map((ind) => (
            <Badge
              key={ind.name}
              variant="secondary"
              style={{ borderColor: ind.color, color: ind.color }}
            >
              {ind.name}
            </Badge>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={selectMode === "buy" ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectMode(selectMode === "buy" ? null : "buy")}
            className={selectMode === "buy" ? "bg-primary" : ""}
          >
            <TrendingUp className="h-4 w-4 mr-1" />
            Select Buy Point
          </Button>
          <Button
            variant={selectMode === "sell" ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectMode(selectMode === "sell" ? null : "sell")}
            className={selectMode === "sell" ? "bg-destructive" : ""}
          >
            <TrendingDown className="h-4 w-4 mr-1" />
            Select Sell Point
          </Button>
          {plPoints.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearPLPoints}>
              Clear Points
            </Button>
          )}
        </div>
      </div>

      {selectMode && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-primary/10 border border-primary/20">
          <MousePointer2 className="h-4 w-4 text-primary" />
          <span className="text-sm">
            Click on the chart to select your{" "}
            <span className={selectMode === "buy" ? "text-primary" : "text-destructive"}>
              {selectMode} point
            </span>
          </span>
        </div>
      )}

      {calculatedPL && (
        <div
          className={`p-4 rounded-lg border ${
            calculatedPL.profit >= 0
              ? "bg-primary/10 border-primary/30"
              : "bg-destructive/10 border-destructive/30"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                <span className="font-semibold">P/L Analysis</span>
              </div>
              <div className="text-sm text-muted-foreground">
                Buy: ${calculatedPL.buyPrice.toFixed(2)} → Sell: ${calculatedPL.sellPrice.toFixed(2)}
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div
                className={`text-2xl font-bold ${
                  calculatedPL.profit >= 0 ? "text-primary" : "text-destructive"
                }`}
              >
                {calculatedPL.profit >= 0 ? "+" : ""}${calculatedPL.profit.toFixed(2)}
              </div>
              <Badge
                variant={calculatedPL.profit >= 0 ? "default" : "destructive"}
                className="text-lg px-3 py-1"
              >
                {calculatedPL.percentage >= 0 ? "+" : ""}
                {calculatedPL.percentage.toFixed(2)}%
              </Badge>
            </div>
          </div>
        </div>
      )}

      <div ref={chartContainerRef} className="w-full h-[500px] rounded-lg border border-border" />
    </div>
  );
}

export type { ChartDataPoint, IndicatorSeries, PLPoint };
