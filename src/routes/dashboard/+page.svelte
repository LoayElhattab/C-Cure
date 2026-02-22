<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import { Chart, registerables } from "chart.js";
  import { theme } from "$lib/theme";

  Chart.register(...registerables);

  let stats = null;
  let loading = true;
  let error = "";

  let cweCanvas;
  let severityCanvas;
  let fileCanvas;
  let confidenceCanvas;

  const SEVERITY_COLORS = {
    Critical: "#ef4444",
    High: "#f97316",
    Medium: "#eab308",
    Low: "#3b82f6",
  };

  onMount(async () => {
    try {
      const raw = await invoke("get_dashboard");
      stats = JSON.parse(raw);
      if (stats.error) {
        error = stats.error;
        loading = false;
        return;
      }
      loading = false;
      setTimeout(() => drawCharts(), 50);
    } catch (err) {
      error = `Failed to load dashboard: ${err}`;
      loading = false;
    }
  });

  function drawCharts() {
    drawCWE();
    drawSeverity();
    drawFiles();
    drawConfidence();
  }

  function drawCWE() {
    if (!cweCanvas || !stats.cwe_counts.length) return;
    new Chart(cweCanvas, {
      type: "bar",
      data: {
        labels: stats.cwe_counts.map((c) => `${c.cwe} — ${c.cwe_name}`),
        datasets: [
          {
            label: "Occurrences",
            data: stats.cwe_counts.map((c) => c.count),
            backgroundColor: stats.cwe_counts.map(
              (c) => SEVERITY_COLORS[c.severity] ?? "#6b7280",
            ),
            borderRadius: 4,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            ticks: { color: $theme === "dark" ? "#9ca3af" : "#6b7280" },
            grid: { color: $theme === "dark" ? "#1f2937" : "#e5e7eb" },
          },
          y: {
            ticks: { color: $theme === "dark" ? "#d1d5db" : "#374151" },
            grid: { display: false },
          },
        },
      },
    });
  }

  function drawSeverity() {
    if (!severityCanvas || !stats.severity_counts.length) return;
    const labels = stats.severity_counts.map((s) => s.severity);
    const data = stats.severity_counts.map((s) => s.count);
    new Chart(severityCanvas, {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            data,
            backgroundColor: labels.map((l) => SEVERITY_COLORS[l] ?? "#6b7280"),
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        cutout: "70%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: $theme === "dark" ? "#9ca3af" : "#6b7280",
              padding: 16,
            },
          },
        },
      },
    });
  }

  function drawFiles() {
    if (!fileCanvas || !stats.file_ratios.length) return;
    new Chart(fileCanvas, {
      type: "bar",
      data: {
        labels: stats.file_ratios.map((f) => f.label),
        datasets: [
          {
            label: "Safe",
            data: stats.file_ratios.map((f) => f.safe),
            backgroundColor: "#22c55e",
            borderRadius: 4,
          },
          {
            label: "Vulnerable",
            data: stats.file_ratios.map((f) => f.vuln),
            backgroundColor: "#ef4444",
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          x: {
            stacked: true,
            ticks: { color: $theme === "dark" ? "#9ca3af" : "#6b7280" },
            grid: { display: false },
          },
          y: {
            stacked: true,
            ticks: { color: $theme === "dark" ? "#9ca3af" : "#6b7280" },
            grid: { color: $theme === "dark" ? "#1f2937" : "#e5e7eb" },
          },
        },
        plugins: {
          legend: {
            labels: { color: $theme === "dark" ? "#9ca3af" : "#6b7280" },
          },
        },
      },
    });
  }

  function drawConfidence() {
    if (!confidenceCanvas) return;
    const bins = stats.confidence_bins;
    new Chart(confidenceCanvas, {
      type: "bar",
      data: {
        labels: ["0–50%", "50–70%", "70–90%", "90–100%"],
        datasets: [
          {
            label: "Predictions",
            data: [
              bins.bin_0_50 ?? 0,
              bins.bin_50_70 ?? 0,
              bins.bin_70_90 ?? 0,
              bins.bin_90_100 ?? 0,
            ],
            backgroundColor: ["#ef4444", "#f97316", "#eab308", "#22c55e"],
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            ticks: { color: $theme === "dark" ? "#9ca3af" : "#6b7280" },
            grid: { display: false },
          },
          y: {
            ticks: { color: $theme === "dark" ? "#9ca3af" : "#6b7280" },
            grid: { color: $theme === "dark" ? "#1f2937" : "#e5e7eb" },
          },
        },
      },
    });
  }
</script>

<div
  class="bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white px-6 py-8 min-h-screen"
>
  <div class="max-w-7xl mx-auto">
    <div class="mb-8">
      <h1 class="text-2xl font-bold">Dashboard</h1>
      <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">
        Aggregate stats across all analyses
      </p>
    </div>

    {#if loading}
      <p class="text-gray-500 dark:text-gray-400 animate-pulse">Loading...</p>
    {:else if error}
      <p class="text-red-500 dark:text-red-400">{error}</p>
    {:else}
      <!-- KPI Row -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        {#each [{ label: "Analyses Run", value: stats.kpis.total_analyses ?? 0, color: "text-cyan-600 dark:text-cyan-400" }, { label: "Functions Scanned", value: stats.kpis.total_functions ?? 0, color: "text-blue-600 dark:text-blue-400" }, { label: "Vulnerable", value: stats.kpis.total_vulnerable ?? 0, color: "text-red-600 dark:text-red-400" }, { label: "Clean", value: stats.kpis.total_safe ?? 0, color: "text-green-600 dark:text-green-400" }] as kpi}
          <div
            class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5"
          >
            <p
              class="text-gray-500 dark:text-gray-400 text-xs uppercase tracking-wide mb-1"
            >
              {kpi.label}
            </p>
            <p class="text-3xl font-bold {kpi.color}">{kpi.value}</p>
          </div>
        {/each}
      </div>

      <!-- CWE + Severity -->
      <div class="grid grid-cols-3 gap-4 mb-4">
        <div
          class="col-span-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5"
        >
          <p
            class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4"
          >
            Vulnerability Breakdown by CWE
          </p>
          {#if stats.cwe_counts.length}
            <canvas bind:this={cweCanvas}></canvas>
          {:else}
            <p
              class="text-gray-500 dark:text-gray-400 text-sm text-center py-8"
            >
              No vulnerable functions yet.
            </p>
          {/if}
        </div>

        <div
          class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex flex-col"
        >
          <p
            class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4"
          >
            Severity Distribution
          </p>
          {#if stats.severity_counts.length}
            <div class="relative flex-1 flex items-center justify-center">
              <canvas bind:this={severityCanvas}></canvas>
              <div
                class="absolute inset-0 flex items-center justify-center pointer-events-none"
              >
                <div class="text-center">
                  <p class="text-2xl font-bold">
                    {stats.kpis.total_vulnerable ?? 0}
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    vulnerable
                  </p>
                </div>
              </div>
            </div>
          {:else}
            <p
              class="text-gray-500 dark:text-gray-400 text-sm text-center py-8"
            >
              No data yet.
            </p>
          {/if}
        </div>
      </div>

      <!-- File ratio + Confidence -->
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div
          class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5"
        >
          <p
            class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4"
          >
            Vulnerable vs Safe per File
          </p>
          {#if stats.file_ratios.length}
            <canvas bind:this={fileCanvas}></canvas>
          {:else}
            <p
              class="text-gray-500 dark:text-gray-400 text-sm text-center py-8"
            >
              No files scanned yet.
            </p>
          {/if}
        </div>

        <div
          class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5"
        >
          <p
            class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1"
          >
            Model Confidence Distribution
          </p>
          <p class="text-xs text-gray-400 dark:text-gray-500 mb-4">
            Low confidence = needs human review
          </p>
          <canvas bind:this={confidenceCanvas}></canvas>
        </div>
      </div>

      <!-- Recent Analyses -->
      <div
        class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden"
      >
        <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-800">
          <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Recent Analyses
          </p>
        </div>
        <table class="w-full text-sm">
          <thead
            class="text-gray-500 dark:text-gray-400 text-xs uppercase border-b border-gray-200 dark:border-gray-800"
          >
            <tr>
              <th class="text-left px-5 py-3">Project</th>
              <th class="text-left px-5 py-3">Date</th>
              <th class="text-left px-5 py-3">Functions</th>
              <th class="text-left px-5 py-3">Vulnerable</th>
              <th class="px-5 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {#each stats.recent_analyses as item}
              <tr
                class="border-b border-gray-200 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <td class="px-5 py-3 font-mono">{item.project_name}</td>
                <td class="px-5 py-3 text-gray-500 dark:text-gray-400"
                  >{item.timestamp}</td
                >
                <td class="px-5 py-3 text-gray-700 dark:text-gray-300"
                  >{item.total_functions ?? 0}</td
                >
                <td class="px-5 py-3">
                  <span
                    class="{(item.vuln_count ?? 0) > 0
                      ? 'text-red-500 dark:text-red-400'
                      : 'text-green-500 dark:text-green-400'} font-semibold"
                  >
                    {(item.vuln_count ?? 0) > 0
                      ? `${item.vuln_count} found`
                      : "Clean"}
                  </span>
                </td>
                <td class="px-5 py-3 text-right">
                  <a
                    href="/report/{item.id}"
                    class="text-cyan-500 dark:text-cyan-400 hover:text-cyan-600 dark:hover:text-cyan-300"
                    >View →</a
                  >
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>
