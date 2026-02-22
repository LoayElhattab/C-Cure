<script lang="ts">
  import { page } from "$app/stores";
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import hljs from "highlight.js/lib/core";
  import cpp from "highlight.js/lib/languages/cpp";
  import { Copy, Check, Download } from "lucide-svelte";
  import { theme } from "$lib/theme";
  import { success, error as errorToast } from "$lib/toast";

  hljs.registerLanguage("cpp", cpp);

  let report: any = null;
  let error = "";
  let loading = true;
  let filter: "all" | "vulnerable" | "safe" = "all";
  let selected: any = null;
  let copied = false;
  let allFunctions: any[] = [];

  $: filtered =
    filter === "all"
      ? allFunctions
      : allFunctions.filter((f) => f.verdict === filter);

  $: highlightedCode = selected?.code
    ? hljs.highlight(selected.code, { language: "cpp" }).value
    : "";

  $: lines = selected?.code ? selected.code.split("\n") : [];

  onMount(async () => {
    const id = $page.params.id ?? "0";
    try {
      const raw = await invoke<string>("get_report", {
        analysisId: parseInt(id),
      });
      const data = JSON.parse(raw);
      if (data.error) {
        error = data.error;
        loading = false;
        return;
      }
      report = data;
      for (const file of data.files) {
        for (const fn of file.functions) {
          allFunctions.push({ ...fn, file_path: file.file_path });
        }
      }
      allFunctions = allFunctions;
      if (allFunctions.length > 0) selected = allFunctions[0];
    } catch (err) {
      error = `Failed to load report: ${err}`;
    }
    loading = false;
  });

  function vulnCount() {
    return allFunctions.filter((f) => f.verdict === "vulnerable").length;
  }

  async function copyCode() {
    if (!selected?.code) return;
    await navigator.clipboard.writeText(selected.code);
    copied = true;
    setTimeout(() => (copied = false), 2000);
  }
</script>

<!-- highlight.js themes -->
<svelte:head>
  <link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css"
    media="(prefers-color-scheme: dark)"
  />
  <link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-light.min.css"
    media="(prefers-color-scheme: light)"
  />
</svelte:head>

{#if loading}
  <div
    class="min-h-screen bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white flex flex-col"
  >
    <!-- Top Bar skeleton -->
    <header
      class="border-b border-gray-200 dark:border-gray-800 px-6 py-4 flex items-center justify-between"
    >
      <div>
        <div
          class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse"
        ></div>
        <div
          class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-48 mt-1 animate-pulse"
        ></div>
      </div>
      <div class="flex gap-3">
        <div
          class="h-7 bg-gray-200 dark:bg-gray-700 rounded w-20 animate-pulse"
        ></div>
        <div
          class="h-7 bg-gray-200 dark:bg-gray-700 rounded-lg w-32 animate-pulse"
        ></div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Left Panel skeleton -->
      <aside
        class="w-72 border-r border-gray-200 dark:border-gray-800 flex flex-col"
      >
        <div class="flex border-b border-gray-200 dark:border-gray-800 text-sm">
          {#each ["all", "vulnerable", "safe"] as _}
            <div class="flex-1 py-2">
              <div
                class="h-4 bg-gray-200 dark:bg-gray-700 rounded mx-auto w-12 animate-pulse"
              ></div>
            </div>
          {/each}
        </div>
        <div class="flex-1 overflow-y-auto">
          {#each Array(5) as _}
            <div
              class="px-4 py-3 border-b border-gray-200 dark:border-gray-800"
            >
              <div
                class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 animate-pulse"
              ></div>
              <div
                class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mt-1 animate-pulse"
              ></div>
            </div>
          {/each}
        </div>
      </aside>

      <!-- Right Panel skeleton -->
      <main class="flex-1 p-6 overflow-y-auto">
        <div class="max-w-3xl">
          <!-- Function Header skeleton -->
          <div class="flex items-start justify-between mb-4">
            <div>
              <div
                class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-40 animate-pulse"
              ></div>
              <div
                class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-64 mt-1 animate-pulse"
              ></div>
              <div
                class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-48 mt-2 animate-pulse"
              ></div>
            </div>
            <div class="flex flex-col items-end gap-2">
              <div
                class="h-5 bg-gray-200 dark:bg-gray-700 rounded-full w-20 animate-pulse"
              ></div>
              <div
                class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse"
              ></div>
            </div>
          </div>

          <!-- Code Viewer skeleton -->
          <div
            class="rounded-xl border border-gray-300 dark:border-gray-700 overflow-hidden"
          >
            <div
              class="flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-300 dark:border-gray-700"
            >
              <div
                class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-8 animate-pulse"
              ></div>
              <div
                class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse"
              ></div>
            </div>
            <div class="h-64 bg-white dark:bg-[#282c34] animate-pulse"></div>
          </div>

          <!-- CWE Warning skeleton -->
          <div
            class="mt-4 h-24 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse"
          ></div>
        </div>
      </main>
    </div>
  </div>
{:else if error}
  <div
    class="min-h-screen bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white flex items-center justify-center"
  >
    <div class="text-center">
      <p class="text-red-500 dark:text-red-400 mb-4">{error}</p>
      <a
        href="/"
        class="text-cyan-500 dark:text-cyan-400 hover:text-cyan-600 dark:hover:text-cyan-300"
        >← Back to Upload</a
      >
    </div>
  </div>
{:else}
  <div
    class="min-h-screen bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white flex flex-col"
  >
    <header
      class="border-b border-gray-200 dark:border-gray-800 px-6 py-4 flex items-center justify-between"
    >
      <div>
        <h1 class="text-lg font-bold text-cyan-600 dark:text-cyan-400">
          {report.project_name}
        </h1>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          {report.timestamp} · {allFunctions.length} functions · {vulnCount()} vulnerable
        </p>
      </div>
      <div class="flex items-center gap-3">
        <a
          href="/history"
          class="text-sm text-gray-500 dark:text-gray-400 hover:text-cyan-500 dark:hover:text-cyan-400 transition-colors"
          >← History</a
        >
        <button
          class="flex items-center gap-2 text-sm bg-gray-200 hover:bg-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100 font-semibold px-4 py-1.5 rounded-lg transition-colors"
          on:click={async () => {
            try {
              const raw = await invoke<string>("generate_pdf", {
                analysisId: parseInt($page.params.id),
              });
              const result = JSON.parse(raw);
              if (result.error) throw new Error(result.error);
              await invoke("open_path", { path: result.path });
              success("Report exported and opened");
            } catch (err) {
              errorToast("Failed to export PDF: " + err);
            }
          }}
        >
          <Download size={14} />
          Export PDF
        </button>
        <a
          href="/"
          class="text-sm bg-cyan-500 hover:bg-cyan-600 dark:hover:bg-cyan-400 text-gray-900 dark:text-gray-950 font-semibold px-4 py-1.5 rounded-lg transition-colors"
        >
          New Analysis
        </a>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <aside
        class="w-72 border-r border-gray-200 dark:border-gray-800 flex flex-col"
      >
        <div class="flex border-b border-gray-200 dark:border-gray-800 text-sm">
          {#each ["all", "vulnerable", "safe"] as f}
            <button
              class="flex-1 py-2 capitalize transition-colors
              {filter === f
                ? 'text-cyan-500 dark:text-cyan-400 border-b-2 border-cyan-500 dark:border-cyan-400'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}"
              on:click={() => {
                filter = f as typeof filter;
              }}>{f}</button
            >
          {/each}
        </div>

        <div class="flex-1 overflow-y-auto">
          {#each filtered as fn}
            <button
              class="w-full text-left px-4 py-3 border-b border-gray-200 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-900 transition-colors
              {selected?.id === fn.id
                ? 'bg-gray-100 dark:bg-gray-900 border-l-2 border-l-cyan-500 dark:border-l-cyan-400'
                : ''}"
              on:click={() => (selected = fn)}
            >
              <p
                class="text-sm font-mono font-medium {fn.verdict ===
                'vulnerable'
                  ? 'text-red-500 dark:text-red-400'
                  : 'text-green-500 dark:text-green-400'}"
              >
                {fn.function_name}
              </p>
              {#if fn.cwe}
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {fn.cwe}
                </p>
              {:else}
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Clean
                </p>
              {/if}
            </button>
          {/each}

          {#if filtered.length === 0}
            <p
              class="text-gray-500 dark:text-gray-400 text-sm text-center mt-8"
            >
              No functions in this filter.
            </p>
          {/if}
        </div>
      </aside>

      <main class="flex-1 p-6 overflow-y-auto">
        {#if selected}
          <div class="max-w-3xl">
            <div class="flex items-start justify-between mb-4">
              <div>
                <h2 class="text-xl font-mono font-bold">
                  {selected.function_name}
                </h2>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {selected.file_path} · lines {selected.start_line}–{selected.end_line}
                </p>
                {#if selected.verdict === "vulnerable"}
                  <p class="text-sm mt-1">
                    <span class="text-red-500 dark:text-red-400 font-semibold"
                      >{selected.cwe}</span
                    >
                    <span class="text-gray-500 dark:text-gray-400">
                      · {selected.cwe_name}</span
                    >
                  </p>
                {:else}
                  <p class="text-sm text-green-500 dark:text-green-400 mt-1">
                    No vulnerabilities detected
                  </p>
                {/if}
              </div>
              <div class="flex flex-col items-end gap-2">
                <span
                  class="px-3 py-1 rounded-full text-xs font-semibold
              {selected.verdict === 'vulnerable'
                    ? 'bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-300'
                    : 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300'}"
                >
                  {selected.verdict}
                </span>
                {#if selected.confidence !== null && selected.confidence !== undefined}
                  <span class="text-xs text-gray-500 dark:text-gray-400">
                    Confidence: {(selected.confidence * 100).toFixed(1)}%
                  </span>
                {/if}
              </div>
            </div>

            <div
              class="rounded-xl border border-gray-300 dark:border-gray-700 overflow-hidden"
            >
              <div
                class="flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-300 dark:border-gray-700"
              >
                <span class="text-xs text-gray-500 dark:text-gray-400 font-mono"
                  >C++</span
                >
                <button
                  on:click={copyCode}
                  class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  {#if copied}
                    <Check size={13} color="#22c55e" />
                    <span class="text-green-500 dark:text-green-400"
                      >Copied!</span
                    >
                  {:else}
                    <Copy size={13} />
                    Copy
                  {/if}
                </button>
              </div>

              <div
                class="flex overflow-x-auto bg-white dark:bg-[#282c34] text-sm font-mono"
              >
                <div
                  class="select-none text-right pr-4 pl-4 py-4 text-gray-400 dark:text-gray-500 border-r border-gray-300 dark:border-gray-700 leading-6 min-w-[3rem]"
                >
                  {#each lines as _, i}
                    <div>{selected.start_line + i}</div>
                  {/each}
                </div>

                <pre class="flex-1 py-4 px-4 leading-6 overflow-x-auto"><code
                    >{@html highlightedCode}</code
                  ></pre>
              </div>
            </div>

            {#if selected.cwe}
              <div
                class="mt-4 bg-red-100 dark:bg-red-950 border border-red-200 dark:border-red-900 rounded-xl p-4 text-sm text-red-600 dark:text-red-300"
              >
                <p class="font-semibold mb-1">
                  ⚠ {selected.cwe} — {selected.cwe_name}
                </p>
                <p class="text-red-500 dark:text-red-400 text-xs">
                  Severity: <span class="font-semibold"
                    >{selected.severity}</span
                  > · Review this function manually and apply appropriate mitigations.
                </p>
              </div>
            {/if}
          </div>
        {/if}
      </main>
    </div>
  </div>
{/if}
