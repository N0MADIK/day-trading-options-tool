import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Settings2, Plus, X, TrendingUp, Activity, BarChart3 } from "lucide-react";

export interface IndicatorConfig {
  id: string;
  name: string;
  type: "sma" | "ema" | "rsi" | "macd" | "bollinger" | "vwap" | "custom";
  enabled: boolean;
  color: string;
  params: Record<string, number>;
}

const defaultIndicators: Omit<IndicatorConfig, "id" | "enabled">[] = [
  {
    name: "SMA (Simple Moving Average)",
    type: "sma",
    color: "#3b82f6",
    params: { period: 20 },
  },
  {
    name: "EMA (Exponential Moving Average)",
    type: "ema",
    color: "#8b5cf6",
    params: { period: 12 },
  },
  {
    name: "RSI (Relative Strength Index)",
    type: "rsi",
    color: "#f59e0b",
    params: { period: 14, overbought: 70, oversold: 30 },
  },
  {
    name: "MACD",
    type: "macd",
    color: "#10b981",
    params: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
  },
  {
    name: "Bollinger Bands",
    type: "bollinger",
    color: "#ec4899",
    params: { period: 20, stdDev: 2 },
  },
  {
    name: "VWAP",
    type: "vwap",
    color: "#06b6d4",
    params: {},
  },
];

interface IndicatorDialogProps {
  activeIndicators: IndicatorConfig[];
  onIndicatorsChange: (indicators: IndicatorConfig[]) => void;
}

export function IndicatorDialog({
  activeIndicators,
  onIndicatorsChange,
}: IndicatorDialogProps) {
  const [open, setOpen] = useState(false);
  const [localIndicators, setLocalIndicators] = useState<IndicatorConfig[]>(activeIndicators);

  const handleAddIndicator = (indicator: Omit<IndicatorConfig, "id" | "enabled">) => {
    const newIndicator: IndicatorConfig = {
      ...indicator,
      id: `${indicator.type}-${Date.now()}`,
      enabled: true,
    };
    setLocalIndicators([...localIndicators, newIndicator]);
  };

  const handleRemoveIndicator = (id: string) => {
    setLocalIndicators(localIndicators.filter((ind) => ind.id !== id));
  };

  const handleToggleIndicator = (id: string) => {
    setLocalIndicators(
      localIndicators.map((ind) =>
        ind.id === id ? { ...ind, enabled: !ind.enabled } : ind
      )
    );
  };

  const handleParamChange = (id: string, param: string, value: number) => {
    setLocalIndicators(
      localIndicators.map((ind) =>
        ind.id === id
          ? { ...ind, params: { ...ind.params, [param]: value } }
          : ind
      )
    );
  };

  const handleColorChange = (id: string, color: string) => {
    setLocalIndicators(
      localIndicators.map((ind) =>
        ind.id === id ? { ...ind, color } : ind
      )
    );
  };

  const handleApply = () => {
    onIndicatorsChange(localIndicators);
    setOpen(false);
  };

  const getIndicatorIcon = (type: string) => {
    switch (type) {
      case "sma":
      case "ema":
        return <TrendingUp className="h-4 w-4" />;
      case "rsi":
      case "macd":
        return <Activity className="h-4 w-4" />;
      case "bollinger":
      case "vwap":
        return <BarChart3 className="h-4 w-4" />;
      default:
        return <TrendingUp className="h-4 w-4" />;
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Settings2 className="h-4 w-4 mr-2" />
          Indicators
          {activeIndicators.filter((i) => i.enabled).length > 0 && (
            <Badge variant="secondary" className="ml-2">
              {activeIndicators.filter((i) => i.enabled).length}
            </Badge>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Technical Indicators</DialogTitle>
          <DialogDescription>
            Add and configure technical indicators for your chart analysis
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium mb-3">Available Indicators</h4>
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-2">
                {defaultIndicators.map((indicator) => (
                  <div
                    key={indicator.type}
                    className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-secondary/50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {getIndicatorIcon(indicator.type)}
                      <span className="text-sm">{indicator.name}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleAddIndicator(indicator)}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>

          <div>
            <h4 className="font-medium mb-3">Active Indicators</h4>
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-3">
                {localIndicators.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No indicators added. Click + to add one.
                  </p>
                ) : (
                  localIndicators.map((indicator) => (
                    <div
                      key={indicator.id}
                      className="p-3 rounded-lg border border-border space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={indicator.enabled}
                            onCheckedChange={() => handleToggleIndicator(indicator.id)}
                          />
                          <span
                            className="text-sm font-medium"
                            style={{ color: indicator.enabled ? indicator.color : undefined }}
                          >
                            {indicator.type.toUpperCase()}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="color"
                            value={indicator.color}
                            onChange={(e) => handleColorChange(indicator.id, e.target.value)}
                            className="w-6 h-6 rounded cursor-pointer"
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveIndicator(indicator.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      {Object.keys(indicator.params).length > 0 && (
                        <>
                          <Separator />
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(indicator.params).map(([param, value]) => (
                              <div key={param} className="space-y-1">
                                <Label className="text-xs capitalize">{param}</Label>
                                <Input
                                  type="number"
                                  value={value}
                                  onChange={(e) =>
                                    handleParamChange(
                                      indicator.id,
                                      param,
                                      parseFloat(e.target.value) || 0
                                    )
                                  }
                                  className="h-8"
                                />
                              </div>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleApply}>Apply Indicators</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
