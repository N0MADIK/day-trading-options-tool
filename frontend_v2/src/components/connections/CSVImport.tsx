import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Upload,
  FileSpreadsheet,
  CheckCircle,
  X,
  Loader2,
  Download,
  HelpCircle,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";

interface ColumnMapping {
  [key: string]: string;
}

const importTypes = [
  { id: "holdings", name: "Holdings", description: "Import portfolio holdings (stocks, bonds, funds)" },
  { id: "transactions", name: "Transactions", description: "Import transaction history" },
  { id: "accounts", name: "Account Balances", description: "Import account balance snapshots" },
];

const holdingsColumns = ["symbol", "name", "quantity", "price", "value", "costBasis", "type"];
const transactionColumns = ["date", "symbol", "type", "quantity", "price", "amount", "description"];
const accountColumns = ["accountName", "type", "balance", "currency"];

export function CSVImport({ onImportComplete }: { onImportComplete?: () => void }) {
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [dialogOpen, setDialogOpen] = useState(false);
  const [importType, setImportType] = useState<string>("transactions");
  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [previewData, setPreviewData] = useState<string[][]>([]);
  const [columnMapping, setColumnMapping] = useState<ColumnMapping>({});
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState<"upload" | "mapping" | "preview" | "complete">("upload");
  const [importResults, setImportResults] = useState<{ success: number; failed: number }>({ success: 0, failed: 0 });
  const [selectedAccountId, setSelectedAccountId] = useState<string>("__create_new__");
  const [accounts, setAccounts] = useState<any[]>([]);
  const [csvSourceName, setCsvSourceName] = useState<string>("");

  const fetchAccounts = async () => {
    if (!user) return;
    const { data } = await supabase
      .from("connected_accounts")
      .select("id, institution_name, account_name, metadata")
      .eq("user_id", user.id);
    setAccounts(data || []);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith(".csv")) {
      toast({
        title: "Invalid File",
        description: "Please select a CSV file",
        variant: "destructive",
      });
      return;
    }

    setFile(selectedFile);
    setCsvSourceName(selectedFile.name.replace('.csv', ''));
    parseCSV(selectedFile);
  };

  const parseCSV = (csvFile: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split(/\r?\n/).filter(line => line.trim());
      
      if (lines.length < 2) {
        toast({
          title: "Invalid CSV",
          description: "File must have headers and at least one data row",
          variant: "destructive",
        });
        return;
      }

      const headerRow = parseCSVLine(lines[0]);
      setHeaders(headerRow);

      const dataRows = lines.slice(1, 6).map(line => parseCSVLine(line));
      setPreviewData(dataRows);

      // Auto-detect import type based on columns
      const hasDate = headerRow.some(h => h.toLowerCase().includes('date'));
      const hasTransactionType = headerRow.some(h => h.toLowerCase().includes('transaction type'));
      
      if (hasDate && hasTransactionType) {
        setImportType("transactions");
      }

      // Enhanced auto-map columns based on common names (including brokerage export formats)
      const mapping: ColumnMapping = {};
      headerRow.forEach((header, index) => {
        const normalized = header.toLowerCase().trim();
        
        // Symbol detection
        if (normalized === "symbol" || normalized === "ticker" || normalized === "stock symbol") {
          mapping.symbol = index.toString();
        }
        // Name detection
        else if (normalized === "investment name" || normalized === "security name" || 
                 normalized === "name" || normalized === "security" || normalized === "description") {
          if (importType === "transactions") {
            mapping.description = index.toString();
          } else {
            mapping.name = index.toString();
          }
        }
        // Transaction description
        else if (normalized === "transaction description") {
          mapping.description = index.toString();
        }
        // Quantity/Shares detection
        else if (normalized === "shares" || normalized === "quantity" || normalized === "units" || normalized === "qty") {
          mapping.quantity = index.toString();
        }
        // Price detection
        else if (normalized === "share price" || normalized === "price" || normalized === "unit price") {
          mapping.price = index.toString();
        }
        // Value/Amount detection  
        else if (normalized === "net amount" || normalized === "amount" || normalized === "total" || 
                 normalized === "value" || normalized === "principal amount" || normalized === "market value") {
          mapping.amount = index.toString();
          mapping.value = index.toString();
        }
        // Cost basis detection
        else if (normalized === "cost basis" || normalized === "basis" || normalized === "cost" || 
                 normalized === "original cost" || normalized === "average cost") {
          mapping.costBasis = index.toString();
        }
        // Type detection
        else if (normalized === "transaction type" || normalized === "type" || normalized === "action" ||
                 normalized === "trade type" || normalized === "activity") {
          mapping.type = index.toString();
        }
        // Date detection
        else if (normalized === "trade date" || normalized === "date" || normalized === "transaction date" ||
                 normalized === "settlement date") {
          mapping.date = index.toString();
        }
        // Balance detection
        else if (normalized === "balance" || normalized === "account balance") {
          mapping.balance = index.toString();
        }
        // Account name detection
        else if (normalized === "account" || normalized === "account name" || normalized === "account number") {
          mapping.accountName = index.toString();
        }
      });
      
      setColumnMapping(mapping);
      setStep("mapping");
    };
    reader.readAsText(csvFile);
  };

  const parseCSVLine = (line: string): string[] => {
    const result: string[] = [];
    let current = "";
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === "," && !inQuotes) {
        result.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  };

  const getColumnsForType = () => {
    switch (importType) {
      case "holdings": return holdingsColumns;
      case "transactions": return transactionColumns;
      case "accounts": return accountColumns;
      default: return [];
    }
  };

  const handleImport = async () => {
    if (!user || !file) return;

    setImporting(true);
    setProgress(0);

    try {
      // First, create or get the CSV source account
      let accountId: string | null = null;
      
      if (selectedAccountId === "__create_new__") {
        // Create a new CSV import source
        const { data: newAccount, error: accountError } = await supabase
          .from("connected_accounts")
          .insert({
            user_id: user.id,
            institution_name: "CSV Import",
            institution_type: "brokerage",
            account_name: csvSourceName || file.name.replace('.csv', ''),
            balance: 0,
            is_connected: true,
            connection_status: "manual",
            metadata: { 
              source: "csv_import", 
              imported_at: new Date().toISOString(),
              file_name: file.name,
            },
          })
          .select()
          .single();

        if (accountError) throw accountError;
        accountId = newAccount.id;
      } else if (selectedAccountId !== "__none__") {
        accountId = selectedAccountId;
      }

      const text = await file.text();
      const lines = text.split(/\r?\n/).filter(line => line.trim());
      const dataLines = lines.slice(1).filter(line => line.trim());
      
      let successCount = 0;
      let failCount = 0;
      let totalBalance = 0;

      for (let i = 0; i < dataLines.length; i++) {
        const values = parseCSVLine(dataLines[i]);
        
        try {
          if (importType === "holdings") {
            const result = await importHolding(values, accountId);
            if (result) totalBalance += result.value;
            successCount++;
          } else if (importType === "transactions") {
            await importTransaction(values, accountId);
            successCount++;
          } else if (importType === "accounts") {
            await importAccount(values);
            successCount++;
          }
        } catch (err) {
          console.error("Import error for row:", values, err);
          failCount++;
        }

        setProgress(Math.round(((i + 1) / dataLines.length) * 100));
      }

      // Update the account balance if we created a new account
      if (accountId && totalBalance > 0) {
        await supabase
          .from("connected_accounts")
          .update({ balance: totalBalance })
          .eq("id", accountId);
      }

      setImportResults({ success: successCount, failed: failCount });
      setStep("complete");

      toast({
        title: "Import Complete",
        description: `Successfully imported ${successCount} records${failCount > 0 ? `, ${failCount} failed` : ""}`,
      });

      onImportComplete?.();
    } catch (error: any) {
      toast({
        title: "Import Failed",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setImporting(false);
    }
  };

  const importHolding = async (values: string[], accountId: string | null) => {
    if (!user) return null;
    
    const symbol = values[parseInt(columnMapping.symbol || "-1")] || "";
    const name = values[parseInt(columnMapping.name || columnMapping.description || "-1")] || symbol;
    const quantity = parseFloat(values[parseInt(columnMapping.quantity || "-1")] || "0");
    const price = parseFloat(values[parseInt(columnMapping.price || "-1")] || "0");
    const value = parseFloat(values[parseInt(columnMapping.value || "-1")] || "0") || (quantity * price);
    const costBasis = parseFloat(values[parseInt(columnMapping.costBasis || "-1")] || "0");
    const type = values[parseInt(columnMapping.type || "-1")] || "stock";

    if (!symbol || quantity === 0) return null;

    const { error } = await supabase.from("holdings").insert({
      user_id: user.id,
      account_id: accountId,
      symbol: symbol.toUpperCase().trim(),
      name: name.trim(),
      quantity: Math.abs(quantity),
      current_price: Math.abs(price),
      market_value: Math.abs(value),
      average_cost: costBasis > 0 ? costBasis / Math.abs(quantity) : Math.abs(price),
      asset_type: type.toLowerCase().includes('cash') ? 'cash' : 'stock',
      unrealized_pnl: value - costBasis,
      unrealized_pnl_percent: costBasis > 0 ? ((value - costBasis) / costBasis) * 100 : 0,
    });

    if (error) throw error;
    return { value: Math.abs(value) };
  };

  const importTransaction = async (values: string[], accountId: string | null) => {
    if (!user) return;
    
    const dateStr = values[parseInt(columnMapping.date || "-1")] || new Date().toISOString();
    const symbol = values[parseInt(columnMapping.symbol || "-1")] || null;
    const rawType = values[parseInt(columnMapping.type || "-1")] || "";
    const quantity = parseFloat(values[parseInt(columnMapping.quantity || "-1")] || "0");
    const price = parseFloat(values[parseInt(columnMapping.price || "-1")] || "0");
    const amount = parseFloat(values[parseInt(columnMapping.amount || "-1")] || "0") || (quantity * price);
    const description = values[parseInt(columnMapping.description || "-1")] || "";

    // Skip empty rows
    if (!dateStr || dateStr === "") return;

    // Normalize transaction type
    let transactionType = "other";
    const typeLower = rawType.toLowerCase();
    if (typeLower.includes("buy") || typeLower.includes("purchase")) {
      transactionType = "buy";
    } else if (typeLower.includes("sell") || typeLower.includes("liquidation")) {
      transactionType = "sell";
    } else if (typeLower.includes("dividend")) {
      transactionType = "dividend";
    } else if (typeLower.includes("reinvestment")) {
      transactionType = "reinvestment";
    } else if (typeLower.includes("deposit") || typeLower.includes("funds received")) {
      transactionType = "deposit";
    } else if (typeLower.includes("withdrawal") || typeLower.includes("sweep out")) {
      transactionType = "withdrawal";
    } else if (typeLower.includes("transfer")) {
      transactionType = "transfer";
    } else if (typeLower.includes("corp action") || typeLower.includes("spinoff")) {
      transactionType = "corporate_action";
    }

    // Parse date
    let parsedDate: Date;
    try {
      parsedDate = new Date(dateStr);
      if (isNaN(parsedDate.getTime())) {
        // Try different date formats
        const parts = dateStr.split(/[-\/]/);
        if (parts.length === 3) {
          parsedDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
        }
      }
    } catch {
      parsedDate = new Date();
    }

    const { error } = await supabase.from("transactions").insert({
      user_id: user.id,
      account_id: accountId,
      transaction_date: parsedDate.toISOString(),
      symbol: symbol?.toUpperCase().trim() || null,
      transaction_type: transactionType,
      quantity: Math.abs(quantity),
      price: Math.abs(price),
      total_amount: amount,
      description: description.trim(),
    });

    if (error) throw error;
  };

  const importAccount = async (values: string[]) => {
    if (!user) return;
    
    const accountName = values[parseInt(columnMapping.accountName || "0")] || "Imported Account";
    const type = values[parseInt(columnMapping.type || "1")] || "brokerage";
    const balance = parseFloat(values[parseInt(columnMapping.balance || "2")] || "0");
    const currency = values[parseInt(columnMapping.currency || "3")] || "USD";

    const { error } = await supabase.from("connected_accounts").insert({
      user_id: user.id,
      institution_name: "CSV Import",
      institution_type: type.toLowerCase(),
      account_name: accountName,
      balance,
      currency,
      is_connected: true,
      connection_status: "manual",
      metadata: { source: "csv_import", imported_at: new Date().toISOString() },
    });

    if (error) throw error;
  };

  const resetImport = () => {
    setFile(null);
    setHeaders([]);
    setPreviewData([]);
    setColumnMapping({});
    setStep("upload");
    setProgress(0);
    setImportResults({ success: 0, failed: 0 });
    setSelectedAccountId("__create_new__");
    setCsvSourceName("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const downloadTemplate = () => {
    let headers: string[] = [];
    let sampleRow: string[] = [];

    if (importType === "holdings") {
      headers = ["Symbol", "Name", "Quantity", "Price", "Value", "Cost Basis", "Type"];
      sampleRow = ["AAPL", "Apple Inc.", "100", "150.00", "15000.00", "12000.00", "stock"];
    } else if (importType === "transactions") {
      headers = ["Trade Date", "Symbol", "Transaction Type", "Shares", "Share Price", "Net Amount", "Transaction Description"];
      sampleRow = ["2024-01-15", "AAPL", "Buy", "10", "150.00", "-1500.00", "Purchase"];
    } else {
      headers = ["Account Name", "Type", "Balance", "Currency"];
      sampleRow = ["My Brokerage", "brokerage", "50000.00", "USD"];
    }

    const csv = [headers.join(","), sampleRow.join(",")].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${importType}_template.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Get CSV import accounts for display
  const csvImportAccounts = accounts.filter(a => {
    const meta = a.metadata as { source?: string } | null;
    return meta?.source === "csv_import";
  });

  return (
    <Dialog open={dialogOpen} onOpenChange={(open) => {
      setDialogOpen(open);
      if (open) {
        fetchAccounts();
      } else {
        resetImport();
      }
    }}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Upload className="h-4 w-4 mr-2" />
          Import CSV
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Import from CSV</DialogTitle>
          <DialogDescription>
            Import your financial data from a CSV file exported from your custodian (Vanguard, Fidelity, Schwab, etc.)
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {step === "upload" && (
            <>
              <div className="space-y-2">
                <Label>Import Type</Label>
                <Select value={importType} onValueChange={setImportType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {importTypes.map((type) => (
                      <SelectItem key={type.id} value={type.id}>
                        <div>
                          <p>{type.name}</p>
                          <p className="text-xs text-muted-foreground">{type.description}</p>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="border-2 border-dashed rounded-lg p-8 text-center">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <FileSpreadsheet className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">Drop your CSV file here</p>
                <p className="text-sm text-muted-foreground mb-4">Supports exports from Vanguard, Fidelity, Schwab, and more</p>
                <Button onClick={() => fileInputRef.current?.click()}>
                  Select CSV File
                </Button>
              </div>

              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Need a template?</span>
                </div>
                <Button variant="outline" size="sm" onClick={downloadTemplate}>
                  <Download className="h-4 w-4 mr-2" />
                  Download Template
                </Button>
              </div>
            </>
          )}

          {step === "mapping" && (
            <>
              <div className="flex items-center gap-2 p-4 bg-primary/10 rounded-lg">
                <FileSpreadsheet className="h-5 w-5 text-primary" />
                <span className="font-medium">{file?.name}</span>
                <Badge variant="secondary">{previewData.length} rows preview</Badge>
                <Button variant="ghost" size="sm" onClick={resetImport} className="ml-auto">
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {importType !== "accounts" && (
                <div className="space-y-2">
                  <Label>Save to Account</Label>
                  <Select value={selectedAccountId} onValueChange={setSelectedAccountId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select or create account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__create_new__">Create new CSV source: {csvSourceName || file?.name}</SelectItem>
                      <SelectItem value="__none__">Don't associate with account</SelectItem>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.institution_name} - {acc.account_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    This will create a data source visible in your Connections page
                  </p>
                </div>
              )}

              <div className="space-y-4">
                <h4 className="font-medium">Map Columns</h4>
                <div className="grid grid-cols-2 gap-4">
                  {getColumnsForType().map((col) => (
                    <div key={col} className="space-y-2">
                      <Label className="capitalize">{col.replace(/([A-Z])/g, " $1").trim()}</Label>
                      <Select
                        value={columnMapping[col] || "__unmapped__"}
                        onValueChange={(value) => setColumnMapping({ ...columnMapping, [col]: value === "__unmapped__" ? "" : value })}
                      >
                        <SelectTrigger className={columnMapping[col] ? "border-primary" : ""}>
                          <SelectValue placeholder="Select column" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="__unmapped__">Not mapped</SelectItem>
                          {headers.map((header, idx) => 
                            header.trim() ? (
                              <SelectItem key={idx} value={idx.toString()}>
                                {header}
                              </SelectItem>
                            ) : null
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">Preview</h4>
                <div className="border rounded-lg overflow-auto max-h-48">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {headers.map((header, idx) => (
                          <TableHead key={idx} className="whitespace-nowrap">
                            {header}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {previewData.map((row, rowIdx) => (
                        <TableRow key={rowIdx}>
                          {row.map((cell, cellIdx) => (
                            <TableCell key={cellIdx} className="whitespace-nowrap">
                              {cell}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </>
          )}

          {step === "complete" && (
            <div className="text-center py-8">
              <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-500" />
              <h3 className="text-xl font-semibold mb-2">Import Complete!</h3>
              <p className="text-muted-foreground mb-4">
                Successfully imported {importResults.success} records
                {importResults.failed > 0 && (
                  <span className="text-destructive"> ({importResults.failed} failed)</span>
                )}
              </p>
              <p className="text-sm text-muted-foreground">
                Your data is now visible in the Dashboard and Financial Breakdown pages.
              </p>
            </div>
          )}

          {importing && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Importing...</span>
                <span className="text-sm font-medium">{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
          )}
        </div>

        <DialogFooter>
          {step === "upload" && (
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
          )}
          {step === "mapping" && (
            <>
              <Button variant="outline" onClick={resetImport}>
                Back
              </Button>
              <Button onClick={handleImport} disabled={importing}>
                {importing && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Import Data
              </Button>
            </>
          )}
          {step === "complete" && (
            <>
              <Button variant="outline" onClick={resetImport}>
                Import More
              </Button>
              <Button onClick={() => setDialogOpen(false)}>
                Done
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
