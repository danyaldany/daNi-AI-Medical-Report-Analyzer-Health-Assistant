"use client";

import { useState, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { useDropzone } from "react-dropzone";
// import ThemeToggle from "@/components/ThemeToggle";
import ThemeToggle from "../components/ThemeToggle";

// ========== TYPES ==========
type ExtractedTest = {
  test_name: string;
  value: string;
  unit: string | null;
  category?: string;
  normal_range?: string;
};

type TestResult = {
  supported: boolean;
  test_name: string;
  category?: string;
  unit?: string;
  reference_range?: string;
  explanation_en?: string;
  explanation_ur?: string;
  message?: string;
  value?: string;
  abnormal_status?: string;
  doctor_questions?: string[];
};

type MedicineResult = {
  supported: boolean;
  medicine_name?: string;
  message?: string;
  generic_name?: string;
  common_brands_pk?: string[];
  category?: string;
  purpose_en?: string;
  purpose_ur?: string;
  general_notes_en?: string;
  general_notes_ur?: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ========== PANEL CONFIG ==========
const PANEL_MAP: Record<string, string> = {
  CBC: "Hematology",
  Hematology: "Hematology",
  "Blood Sugar": "Bio-Chemistry",
  "Lipid Profile": "Bio-Chemistry",
  "Liver Function": "Bio-Chemistry",
  "Kidney Function": "Bio-Chemistry",
  Biochemistry: "Bio-Chemistry",
  "Bio-Chemistry": "Bio-Chemistry",
  Serology: "Serology",
  "Infectious Diseases": "Serology",
};

const PANEL_ORDER = ["Bio-Chemistry", "Serology", "Hematology"];
const PANEL_STYLES: Record<string, { border: string; icon: string; color: string }> = {
  Hematology: { border: "border-red-500", icon: "🩸", color: "#ef4444" },
  "Bio-Chemistry": { border: "border-blue-500", icon: "🧪", color: "#3b82f6" },
  Serology: { border: "border-purple-500", icon: "🔬", color: "#8b5cf6" },
};

function panelFor(category?: string, testName?: string) {
  const normalized = `${category || ""} ${testName || ""}`.toLowerCase();
  if (PANEL_MAP[category || ""]) return PANEL_MAP[category || ""];
  if (/hematology|hematologic|cbc|blood count|hemoglobin|platelet|neutrophil|lymphocyte|erythrocyte/.test(normalized)) {
    return "Hematology";
  }
  if (/serology|serologic|antibody|antigen|infection|hepatitis|hiv|dengue|typhoid|malaria/.test(normalized)) {
    return "Serology";
  }
  return "Bio-Chemistry";
}

function groupByPanel<T>(items: T[], getCategory: (item: T) => string | undefined, getTestName?: (item: T) => string | undefined) {
  const groups: Record<string, T[]> = {};
  for (const item of items) {
    const panel = panelFor(getCategory(item), getTestName?.(item));
    if (!groups[panel]) groups[panel] = [];
    groups[panel].push(item);
  }
  return PANEL_ORDER.map((p) => [p, groups[p] || []] as const);
}

function statusLabel(status?: string) {
  if (status === "normal") return { text: "✅ Within range", color: "var(--normal)" };
  if (status === "abnormal_low" || status === "abnormal_high")
    return { text: "⚠️ Outside range", color: "var(--abnormal)" };
  if (status === "range_unclear") return { text: "📊 Compare manually", color: "var(--unclear)" };
  if (status === "value_unparseable") return { text: "❓ Format error", color: "var(--unclear)" };
  return null;
}

function displayUnit(unit?: string | null) {
  return !unit || unit.trim() === "" || unit === "None" ? "—" : unit;
}

function LoadingSpinner() {
  return <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" aria-label="Loading" />;
}

// ========== MAIN COMPONENT ==========
export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [extracted, setExtracted] = useState<ExtractedTest[]>([]);
  const [rawText, setRawText] = useState("");
  const [hasExtractedOnce, setHasExtractedOnce] = useState(false);
  const [results, setResults] = useState<TestResult[] | null>(null);
  const [medicines, setMedicines] = useState<string[]>([]);
  const [medicineResults, setMedicineResults] = useState<MedicineResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"upload" | "results">("upload");
  const [activePanel, setActivePanel] = useState<string>("Bio-Chemistry");

  // ===== Drag & Drop =====
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setFile(acceptedFiles[0]);
  }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
      onDrop,
    accept: { "image/*": [], "application/pdf": [] },
    maxFiles: 1,
  });

  // ===== API Calls =====
  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE}/ocr/extract`, { method: "POST", body: formData });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      const data = await res.json();
      const entries = data.extracted_tests || [];
      setExtracted(entries);
      setRawText(data.raw_text || "");
      setHasExtractedOnce(true);
      setActiveTab("upload");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const testsToSend = extracted
        .filter((e) => e.test_name.trim() !== "")
        .map((e) => ({
          test_name: e.test_name,
          value: e.value || "",
          normal_range: e.normal_range || "",
        }));

      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tests: testsToSend,
          medicines: medicines.filter((m) => m.trim()),
        }),
      });
      if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
      const data = await res.json();
      setResults(data.tests || []);
      setMedicineResults(data.medicines || []); // ← YEH ADD KARO
      setActiveTab("results");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function updateField(index: number, field: keyof ExtractedTest, value: string) {
    setExtracted((prev) => prev.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  }

  function removeRow(index: number) {
    setExtracted((prev) => prev.filter((_, i) => i !== index));
  }

  function addRow() {
    setExtracted((prev) => [
      ...prev,
      {
        test_name: "",
        value: "",
        unit: "",
        normal_range: "",
        category: activePanel,
      },
    ]);
  }
function updateMedicine(index: number, value: string) {
  setMedicines((prev) => prev.map((m, i) => (i === index ? value : m)));
}

function addMedicineRow() {
  setMedicines((prev) => [...prev, ""]);
}

function removeMedicineRow(index: number) {
  setMedicines((prev) => prev.filter((_, i) => i !== index));
}
  function startOver() {
    setFile(null);
    setExtracted([]);
    setResults(null);
    setHasExtractedOnce(false);
    setError(null);
    setActiveTab("upload");
    setActivePanel("Bio-Chemistry");
  }

  // ===== Chart Data Preparation =====
    const prepareChartData = () => {
  if (!results) return { barData: [], pieData: [] };

  // ✅ Type guard: ensure value is a non-empty string
  const testsWithValues = results.filter(
    (r): r is TestResult & { value: string } =>
      typeof r.value === "string" && r.value.trim() !== "" && r.value !== "N/A"
  );

  // Bar chart data – sirf numeric + simple range
  const barData = testsWithValues
    .filter((r) => {
      const num = parseFloat(r.value);
      if (isNaN(num)) return false;
      const range = r.reference_range || "";
      return /^\d+\.?\d*\s*-\s*\d+\.?\d*$/.test(range.trim());
    })
    .map((r) => ({
      name: r.test_name.length > 12 ? r.test_name.slice(0, 10) + "..." : r.test_name,
      value: parseFloat(r.value), // ab safe hai
      range: parseFloat(r.reference_range?.split("-")?.[1] || "100") || 100,
      rangeMin: parseFloat(r.reference_range?.split("-")?.[0] || "0") || 0,
    }));

  // Pie chart data
  const normal = testsWithValues.filter(
    (r) => r.supported && r.abnormal_status === "normal"
  ).length;
  const abnormal = testsWithValues.filter(
    (r) => r.supported && r.abnormal_status?.startsWith("abnormal")
  ).length;
  const unclear = testsWithValues.filter(
    (r) => r.supported &&
    (r.abnormal_status === "range_unclear" || r.abnormal_status === "value_unparseable")
  ).length;

  const pieData = [
    { name: "Normal", value: normal },
    { name: "Abnormal", value: abnormal },
    { name: "Unclear", value: unclear },
  ].filter((d) => d.value > 0);

  return { barData, pieData };
};

  const { barData, pieData } = prepareChartData();
  const COLORS = ["#4c7a52", "#a6432c", "#a67a2e"];

  // ===== Render Result Card =====
  const renderResultCard = (r: TestResult, idx: number) => {
    const label = r.supported ? statusLabel(r.abnormal_status) : null;
    const hasValue = r.value && r.value.trim() !== "" && r.value !== "N/A";
    return (
      <div
        key={idx}
        className={`p-4 glass ${r.supported ? `status-bar--${r.abnormal_status || "unclear"}` : ""}`}
      >
        <p className="font-bold text-lg" style={{ color: "var(--foreground)" }}>
          {r.test_name}
        </p>
        {r.supported && hasValue ? (
          <>
            <p className="text-sm text-muted">
              Range: {r.reference_range} {displayUnit(r.unit)}
            </p>
            {label && (
              <p className="text-sm font-medium mt-1">
                Your value: {r.value} {displayUnit(r.unit)} —{" "}
                <span style={{ color: label.color }}>{label.text}</span>
              </p>
            )}
            <p className="text-sm mt-2 leading-relaxed">{r.explanation_en}</p>
            <p className="font-urdu text-sm mt-1" dir="rtl">
              {r.explanation_ur}
            </p>
            {r.doctor_questions && r.doctor_questions.length > 0 && (
              <div className="mt-3 pt-2 border-t border-border">
                <p className="text-xs font-medium text-muted">Questions to ask your doctor</p>
                <ul className="text-xs mt-1 space-y-0.5 text-muted">
                  {r.doctor_questions.map((q, qi) => (
                    <li key={qi}>— {q}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-muted mt-1">
            {r.supported ? "No value provided." : r.message || "Not in our verified database."}
          </p>
        )}
      </div>
    );
  };

  // ===== MAIN RENDER =====
  return (
    <main className="min-h-screen" style={{ background: "var(--background)", color: "var(--foreground)" }}>
      {/* ===== NAVBAR ===== */}
      <nav className="sticky top-0 z-50 glass px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full" style={{ background: "var(--teal)" }} />
          <h1 className="font-display text-xl font-semibold">Sehat Samjho</h1>
          <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: "var(--border-color)" }}>
            AI
          </span>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setActiveTab("upload")}
            className="text-sm font-medium hover:opacity-70 transition"
          >
            Upload
          </button>
          <button
            onClick={() => setActiveTab("results")}
            className="text-sm font-medium hover:opacity-70 transition"
            disabled={!results}
          >
            Results
          </button>
          <ThemeToggle />
        </div>
      </nav>

      {/* ===== HERO SECTION (Always visible) ===== */}
      <section className="max-w-5xl mx-auto px-6 py-10 text-center">
        <h2 className="font-display text-4xl md:text-5xl font-bold leading-tight">
          AI Medical Report Analyzer
        </h2>
        <p className="text-lg mt-3 max-w-2xl mx-auto" style={{ color: "var(--text-muted)" }}>
          Upload your lab report. Get instant, bilingual explanations in English & Urdu.
          <br />
          <span className="text-sm">Understand your health — no medical degree required.</span>
        </p>
        <div className="mt-4 flex justify-center gap-3 text-xs flex-wrap">
          <span className="px-3 py-1 rounded-full" style={{ background: "var(--hematology)", color: "white" }}>
            Hematology
          </span>
          <span className="px-3 py-1 rounded-full" style={{ background: "var(--biochemistry)", color: "white" }}>
            Bio-Chemistry
          </span>
          <span className="px-3 py-1 rounded-full" style={{ background: "var(--serology)", color: "white" }}>
            Serology
          </span>
        </div>
      </section>

      {/* ===== UPLOAD SECTION ===== */}
      {activeTab === "upload" && (
        <section className="max-w-4xl mx-auto px-6 pb-10 space-y-6">
          <div
            {...getRootProps()}
            className={`glass p-10 text-center cursor-pointer transition-all border-2 border-dashed ${
              isDragActive ? "border-teal-500" : "border-border"
            }`}
          >
            <input {...getInputProps()} />
            {file ? (
              <div>
                <p className="text-lg font-medium">📄 {file.name}</p>
                <p className="text-sm text-muted">{(file.size / 1024).toFixed(0)} KB</p>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="mt-2 text-sm text-red-500 hover:underline"
                >
                  Remove file
                </button>
              </div>
            ) : (
              <div>
                <p className="text-4xl mb-2">📤</p>
                <p className="font-medium">Drop your report here, or click to browse</p>
                <p className="text-sm text-muted">Supports JPG, PNG, PDF</p>
              </div>
            )}
          </div>

          <div className="flex gap-4 flex-wrap">
            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className="px-6 py-2.5 rounded-lg font-medium text-white transition disabled:opacity-40 inline-flex items-center gap-2"
              style={{ background: "var(--teal)" }}
            >
              {loading ? <><LoadingSpinner /> Extracting...</> : "🔍 Extract Data"}
            </button>
            <button onClick={startOver} className="px-6 py-2.5 text-sm text-muted hover:underline">
              Start Over
            </button>
          </div>

          {error && <p className="text-sm" style={{ color: "var(--abnormal)" }}>{error}</p>}

          {/* ===== EDIT TABLE ===== */}
          {hasExtractedOnce && (
            <div className="glass p-5 space-y-4">
              <h3 className="font-semibold">Confirm Extracted Values</h3>
              {extracted.length === 0 ? (
                <p className="text-sm text-muted py-4">
                  No values automatically detected. Please add tests manually using the button below.
                </p>
              ) : (
                (() => {
                  const groupedPanels = groupByPanel(
                    extracted.map((r, i) => ({ ...r, _idx: i })),
                    (r) => r.category,
                    (r) => r.test_name
                  );
                  const activeRows = groupedPanels.find(([panel]) => panel === activePanel)?.[1] || [];

                  return (
                    <>
                      {/* Panel Tabs */}
                      <div className="flex gap-4 overflow-x-auto border-b border-border" role="tablist">
                        {groupedPanels.map(([panel, rows]) => {
                          const style = PANEL_STYLES[panel];
                          const isActive = panel === activePanel;
                          return (
                            <button
                              key={panel}
                              type="button"
                              role="tab"
                              aria-selected={isActive}
                              disabled={rows.length === 0}
                              onClick={() => setActivePanel(panel)}
                              className={`shrink-0 border-b-2 px-3 pb-2 text-sm font-semibold transition-colors ${
                                isActive
                                  ? "border-teal-500 bg-teal-600 text-white"
                                  : "border-transparent text-muted hover:border-border hover:text-foreground"
                              } ${rows.length === 0 ? "cursor-not-allowed opacity-40" : ""}`}
                            >
                              {style.icon} {panel}
                            </button>
                          );
                        })}
                      </div>

                      {/* Table */}
                      <div className="overflow-x-auto">
                        {activeRows.length === 0 ? (
                          <p className="py-4 text-sm text-muted">No tests detected in this category.</p>
                        ) : (
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-border text-left text-muted">
                                <th className="py-1 font-medium">Test</th>
                                <th className="font-medium">Value</th>
                                <th className="font-medium">Range</th>
                                <th className="font-medium">Unit</th>
                              </tr>
                            </thead>
                            <tbody>
                              {activeRows.map((row) => (
                                <tr key={row._idx} className="border-b border-border/50">
                                  <td className="py-1">
                                    <input
                                      className="w-full bg-transparent px-1 py-0.5 border-0 border-b border-transparent hover:border-border focus:border-teal-500 focus:outline-none transition-colors"
                                      value={row.test_name ?? ""}
                                      onChange={(e) => updateField(row._idx, "test_name", e.target.value)}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      className="w-24 bg-transparent px-1 py-0.5 border-0 border-b border-transparent hover:border-border focus:border-teal-500 focus:outline-none transition-colors"
                                      placeholder="N/A"
                                      value={row.value ?? ""}
                                      onChange={(e) => updateField(row._idx, "value", e.target.value)}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      className="w-28 bg-transparent px-1 py-0.5 border-0 border-b border-transparent hover:border-border focus:border-teal-500 focus:outline-none transition-colors"
                                      placeholder="e.g. 10-20"
                                      value={row.normal_range ?? ""}
                                      onChange={(e) => updateField(row._idx, "normal_range", e.target.value)}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      className="w-20 bg-transparent px-1 py-0.5 border-0 border-b border-transparent hover:border-border focus:border-teal-500 focus:outline-none transition-colors"
                                      placeholder="Unit"
                                      value={row.unit ?? ""}
                                      onChange={(e) => updateField(row._idx, "unit", e.target.value)}
                                    />
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>
                    </>
                  );
                })()
              )}

              {/* ===== MEDICINES SECTION ===== */}
              <div className="pt-3 border-t border-border">
                <h3 className="text-sm font-medium mb-2" style={{ color: "var(--ink)" }}>
                  💊 Medicines mentioned on this report{" "}
                  <span className="font-normal" style={{ color: "var(--ink-soft)" }}>
                    (optional)
                  </span>
                </h3>
                {medicines.map((m, i) => (
                  <div key={i} className="flex gap-2 mb-1.5">
                    <input
                      className="px-2 py-1 text-sm flex-1 bg-transparent border border-border rounded"
                      placeholder="e.g. Panadol"
                      value={m}
                      onChange={(e) => updateMedicine(i, e.target.value)}
                    />
                    <button
                      onClick={() => removeMedicineRow(i)}
                      className="text-xs text-muted hover:text-red-500"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={addMedicineRow}
                  className="text-sm text-teal-600 hover:underline"
                >
                  + Add a medicine
                </button>
              </div>

              {/* ===== BUTTONS ===== */}
              <div className="flex items-center gap-4">
                <button
                  onClick={handleAnalyze}
                  disabled={loading || extracted.length === 0}
                  className="px-6 py-2.5 rounded-lg font-medium text-white transition inline-flex items-center gap-2 disabled:opacity-40"
                  style={{ background: "var(--teal)" }}
                >
                  {loading ? <><LoadingSpinner /> Analyzing...</> : "📊 Analyze Report (نتائج دیکھیں)"}
                </button>
                <button
                  type="button"
                  onClick={addRow}
                  className="text-sm text-teal-600 hover:underline"
                  style={{ color: "var(--teal)" }}
                >
                  + Add Test Manually (ٹیسٹ شامل کریں)
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      {/* ===== RESULTS DASHBOARD ===== */}
      {activeTab === "results" && results && (
        <section className="max-w-6xl mx-auto px-6 pb-10 space-y-8">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Total Tests = sirf woh jin ki value hai (chahe supported ho ya nahi) */}
          <div className="glass p-4 text-center">
            <p className="text-3xl font-bold">{results.filter((r) => r.value && r.value.trim() !== "" && r.value !== "N/A").length}</p>
            <p className="text-xs text-muted">Total Tests</p>
          </div>
          {/* Normal = supported + value + normal */}
          <div className="glass p-4 text-center" style={{ borderTop: "4px solid var(--normal)" }}>
            <p className="text-3xl font-bold" style={{ color: "var(--normal)" }}>
              {results.filter((r) => r.value && r.supported && r.abnormal_status === "normal").length}
            </p>
            <p className="text-xs text-muted">Normal</p>
          </div>
          {/* Abnormal = supported + value + abnormal */}
          <div className="glass p-4 text-center" style={{ borderTop: "4px solid var(--abnormal)" }}>
            <p className="text-3xl font-bold" style={{ color: "var(--abnormal)" }}>
              {results.filter((r) => r.value && r.supported && r.abnormal_status?.startsWith("abnormal")).length}
            </p>
            <p className="text-xs text-muted">Abnormal</p>
          </div>
          {/* Unclear = supported + value + range_unclear / value_unparseable */}
          <div className="glass p-4 text-center" style={{ borderTop: "4px solid var(--unclear)" }}>
            <p className="text-3xl font-bold" style={{ color: "var(--unclear)" }}>
              {results.filter((r) => r.value && r.supported && (r.abnormal_status === "range_unclear" || r.abnormal_status === "value_unparseable")).length}
            </p>
            <p className="text-xs text-muted">Unclear</p>
          </div>
        </div>

          {/* Charts */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Bar Chart */}
            <div className="glass p-4">
              <h4 className="font-semibold text-sm mb-2">📊 Values vs Reference Range</h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="var(--text-muted)" />
                  <YAxis stroke="var(--text-muted)" />
                  <Tooltip />
                  <Bar dataKey="value" fill="var(--teal)" name="Your Value" />
                  <Bar dataKey="range" fill="var(--abnormal)" name="Upper Range" opacity={0.3} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Pie Chart */}
            {/* Pie Chart */}
              {/* Pie Chart */}
                <div className="glass p-4">
                  <h4 className="font-semibold text-sm mb-2">🧩 Overall Health Status</h4>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="value"
                        label={(props: any) => `${props.name} ${(props.percent * 100).toFixed(0)}%`}
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
          </div>

          {/* Detailed Results Grouped by Panel */}
          {(() => {
            // ✅ Same type guard
            const valueTests = results.filter(
              (r): r is TestResult & { value: string } =>
                typeof r.value === "string" && r.value.trim() !== "" && r.value !== "N/A"
            );

            const supported = valueTests.filter((r) => r.supported);
            const unsupported = valueTests.filter((r) => !r.supported);

            return (
              <>
                {groupByPanel(supported, (r) => r.category, (r) => r.test_name).map(([panel, items]) => {
                  const style = PANEL_STYLES[panel];
                  return (
                    <div key={panel} className="space-y-3">
                      <div className="flex items-center gap-2 border-b pb-2 border-border">
                        <span className="text-2xl">{style.icon}</span>
                        <h3 className="font-bold text-lg">{panel}</h3>
                        <span className="text-xs text-muted ml-auto">{items.length} tests</span>
                      </div>
                      <div className="grid md:grid-cols-2 gap-4">
                        {items.map((r, i) => renderResultCard(r, i))}
                      </div>
                    </div>
                  );
                })}

                {unsupported.length > 0 && (
                  <div className="space-y-3">
                    <div className="border-b pb-2 border-border">
                      <h3 className="font-bold text-lg text-muted">📋 Not in Verified Database</h3>
                      <p className="text-xs text-muted mt-1">
                        These tests were included, but we don't have verified reference data for them yet — no status is shown, by design.
                      </p>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      {unsupported.map((r, i) => renderResultCard(r, i))}
                    </div>
                  </div>
                )}
              </>
            );
          })()}


                    {/* ===== MEDICINE RESULTS ===== */}
          {medicineResults && medicineResults.length > 0 && (
            <div className="pt-4 space-y-3">
              <h3 className="text-sm font-medium" style={{ color: "var(--ink-soft)" }}>
                💊 Medicines
              </h3>
              {medicineResults.map((m, i) => (
                <div
                  key={i}
                  className="pl-4 py-3 glass"
                  style={{ borderLeft: "3px solid var(--teal)" }}
                >
                  <p className="font-medium" style={{ color: "var(--foreground)" }}>
                    {m.medicine_name || m.generic_name}
                  </p>
                  {m.supported ? (
                    <>
                      {m.common_brands_pk && m.common_brands_pk.length > 0 && (
                        <p className="text-xs text-muted">
                          Common brands in Pakistan: {m.common_brands_pk.join(", ")}
                        </p>
                      )}
                      <p className="text-sm mt-1">{m.purpose_en}</p>
                      <p className="font-urdu text-sm mt-1" dir="rtl">
                        {m.purpose_ur}
                      </p>
                      <p className="text-xs mt-1 text-muted">{m.general_notes_en}</p>
                      <p className="font-urdu text-xs mt-1 text-muted" dir="rtl">
                        {m.general_notes_ur}
                      </p>
                    </>
                  ) : (
                    <p className="text-sm text-muted mt-1">{m.message}</p>
                  )}
                </div>
              ))}
            </div>
          )}

                <p className="text-xs italic pt-4 text-muted text-center">
            This is not a substitute for professional medical advice. Please consult a doctor.
          </p>
        </section>
      )}
    </main>
  );
}