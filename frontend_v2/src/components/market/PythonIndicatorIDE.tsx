import { useState } from "react";
import Editor from "@monaco-editor/react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "@/hooks/use-toast";
import { Code2, Play, Save, Trash2, FileCode } from "lucide-react";

export interface CustomIndicatorScript {
  id: string;
  name: string;
  code: string;
  color: string;
  createdAt: Date;
}

interface PythonIndicatorIDEProps {
  scripts: CustomIndicatorScript[];
  onScriptsChange: (scripts: CustomIndicatorScript[]) => void;
  onRunScript: (script: CustomIndicatorScript) => void;
}

const defaultTemplate = `# Custom Indicator Script
# Available variables:
# - prices: list of price data (OHLCV)
# - close: list of closing prices
# - open: list of opening prices
# - high: list of high prices
# - low: list of low prices
# - volume: list of volume data

def calculate_indicator(close, period=14):
    """
    Calculate your custom indicator here.
    Return a list of values matching the length of the input data.
    """
    result = []
    
    # Example: Simple Moving Average
    for i in range(len(close)):
        if i < period - 1:
            result.append(None)
        else:
            avg = sum(close[i-period+1:i+1]) / period
            result.append(avg)
    
    return result

# Run the indicator
indicator_values = calculate_indicator(close, period=20)
`;

const exampleScripts = [
  {
    name: "Custom RSI",
    code: `# Relative Strength Index (RSI)
def calculate_rsi(close, period=14):
    result = []
    gains = []
    losses = []
    
    for i in range(1, len(close)):
        change = close[i] - close[i-1]
        gains.append(max(0, change))
        losses.append(abs(min(0, change)))
    
    for i in range(len(close)):
        if i < period:
            result.append(None)
        else:
            avg_gain = sum(gains[i-period:i]) / period
            avg_loss = sum(losses[i-period:i]) / period
            if avg_loss == 0:
                result.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                result.append(rsi)
    
    return result

indicator_values = calculate_rsi(close, period=14)`,
  },
  {
    name: "Price Momentum",
    code: `# Price Momentum Indicator
def calculate_momentum(close, period=10):
    result = []
    
    for i in range(len(close)):
        if i < period:
            result.append(None)
        else:
            momentum = ((close[i] - close[i-period]) / close[i-period]) * 100
            result.append(momentum)
    
    return result

indicator_values = calculate_momentum(close, period=10)`,
  },
  {
    name: "Average True Range",
    code: `# Average True Range (ATR)
def calculate_atr(high, low, close, period=14):
    result = []
    true_ranges = []
    
    for i in range(len(close)):
        if i == 0:
            tr = high[i] - low[i]
        else:
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
        true_ranges.append(tr)
    
    for i in range(len(close)):
        if i < period - 1:
            result.append(None)
        else:
            atr = sum(true_ranges[i-period+1:i+1]) / period
            result.append(atr)
    
    return result

indicator_values = calculate_atr(high, low, close, period=14)`,
  },
];

export function PythonIndicatorIDE({
  scripts,
  onScriptsChange,
  onRunScript,
}: PythonIndicatorIDEProps) {
  const [open, setOpen] = useState(false);
  const [currentScript, setCurrentScript] = useState<CustomIndicatorScript>({
    id: "",
    name: "New Indicator",
    code: defaultTemplate,
    color: "#3b82f6",
    createdAt: new Date(),
  });
  const [activeTab, setActiveTab] = useState("editor");

  const handleSaveScript = () => {
    if (!currentScript.name.trim()) {
      toast({
        title: "Error",
        description: "Please enter a name for your indicator",
        variant: "destructive",
      });
      return;
    }

    const newScript: CustomIndicatorScript = {
      ...currentScript,
      id: currentScript.id || `custom-${Date.now()}`,
      createdAt: currentScript.id ? currentScript.createdAt : new Date(),
    };

    const existingIndex = scripts.findIndex((s) => s.id === newScript.id);
    if (existingIndex >= 0) {
      const updated = [...scripts];
      updated[existingIndex] = newScript;
      onScriptsChange(updated);
    } else {
      onScriptsChange([...scripts, newScript]);
    }

    toast({
      title: "Saved",
      description: `Indicator "${newScript.name}" has been saved`,
    });
  };

  const handleRunScript = () => {
    if (!currentScript.code.trim()) {
      toast({
        title: "Error",
        description: "Please write some code first",
        variant: "destructive",
      });
      return;
    }

    onRunScript(currentScript);
    toast({
      title: "Indicator Applied",
      description: `Running "${currentScript.name}" on chart`,
    });
  };

  const handleDeleteScript = (id: string) => {
    onScriptsChange(scripts.filter((s) => s.id !== id));
    if (currentScript.id === id) {
      setCurrentScript({
        id: "",
        name: "New Indicator",
        code: defaultTemplate,
        color: "#3b82f6",
        createdAt: new Date(),
      });
    }
    toast({
      title: "Deleted",
      description: "Indicator has been removed",
    });
  };

  const handleLoadScript = (script: CustomIndicatorScript) => {
    setCurrentScript(script);
    setActiveTab("editor");
  };

  const handleLoadExample = (example: { name: string; code: string }) => {
    setCurrentScript({
      id: "",
      name: example.name,
      code: example.code,
      color: "#3b82f6",
      createdAt: new Date(),
    });
    setActiveTab("editor");
  };

  const handleNewScript = () => {
    setCurrentScript({
      id: "",
      name: "New Indicator",
      code: defaultTemplate,
      color: "#3b82f6",
      createdAt: new Date(),
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Code2 className="h-4 w-4 mr-2" />
          Custom Script
          {scripts.length > 0 && (
            <Badge variant="secondary" className="ml-2">
              {scripts.length}
            </Badge>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[85vh]">
        <DialogHeader>
          <DialogTitle>Custom Indicator IDE</DialogTitle>
          <DialogDescription>
            Write Python scripts to create custom technical indicators
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="editor">Editor</TabsTrigger>
            <TabsTrigger value="saved">Saved Scripts</TabsTrigger>
            <TabsTrigger value="examples">Examples</TabsTrigger>
          </TabsList>

          <TabsContent value="editor" className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Label htmlFor="indicator-name">Indicator Name</Label>
                <Input
                  id="indicator-name"
                  value={currentScript.name}
                  onChange={(e) =>
                    setCurrentScript({ ...currentScript, name: e.target.value })
                  }
                  placeholder="My Custom Indicator"
                />
              </div>
              <div>
                <Label>Color</Label>
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="color"
                    value={currentScript.color}
                    onChange={(e) =>
                      setCurrentScript({ ...currentScript, color: e.target.value })
                    }
                    className="w-10 h-10 rounded cursor-pointer"
                  />
                </div>
              </div>
            </div>

            <div className="border border-border rounded-lg overflow-hidden">
              <Editor
                height="350px"
                defaultLanguage="python"
                theme="vs-dark"
                value={currentScript.code}
                onChange={(value) =>
                  setCurrentScript({ ...currentScript, code: value || "" })
                }
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: "on",
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                }}
              />
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={handleNewScript}>
                New Script
              </Button>
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleSaveScript}>
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
                <Button onClick={handleRunScript}>
                  <Play className="h-4 w-4 mr-2" />
                  Run on Chart
                </Button>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="saved">
            <ScrollArea className="h-[400px]">
              {scripts.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <FileCode className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No saved scripts yet</p>
                  <p className="text-sm">Create and save your first custom indicator</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {scripts.map((script) => (
                    <div
                      key={script.id}
                      className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-secondary/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-4 h-4 rounded"
                          style={{ backgroundColor: script.color }}
                        />
                        <div>
                          <p className="font-medium">{script.name}</p>
                          <p className="text-xs text-muted-foreground">
                            Created: {new Date(script.createdAt).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleLoadScript(script)}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onRunScript(script)}
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteScript(script.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          <TabsContent value="examples">
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {exampleScripts.map((example, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-secondary/50 transition-colors"
                  >
                    <div>
                      <p className="font-medium">{example.name}</p>
                      <p className="text-xs text-muted-foreground">
                        Example template
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleLoadExample(example)}
                    >
                      Load in Editor
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
