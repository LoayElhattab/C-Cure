<script lang="ts">
  import { page } from '$app/stores';
  import { invoke } from '@tauri-apps/api/core';
  import { onMount } from 'svelte';

  let report: any = null;
  let error = '';
  let loading = true;
  let filter: 'all' | 'vulnerable' | 'safe' = 'all';
  let selected: any = null;

  // Flatten all functions from all files into one list
  let allFunctions: any[] = [];

  $: filtered = filter === 'all'
    ? allFunctions
    : allFunctions.filter(f => f.verdict === filter);

  onMount(async () => {
    const id = $page.params.id;
    try {
      const raw = await invoke<string>('get_report', { analysisId: parseInt(id) });
      const data = JSON.parse(raw);

      if (data.error) {
        error = data.error;
        loading = false;
        return;
      }

      report = data;

      // Flatten functions, attach file_path to each
      for (const file of data.files) {
        for (const fn of file.functions) {
          allFunctions.push({ ...fn, file_path: file.file_path });
        }
      }
      allFunctions = allFunctions; // trigger reactivity

      if (allFunctions.length > 0) selected = allFunctions[0];

    } catch (err) {
      error = `Failed to load report: ${err}`;
    }
    loading = false;
  });

  function vulnCount() {
    return allFunctions.filter(f => f.verdict === 'vulnerable').length;
  }
</script>

{#if loading}
  <div class="min-h-screen bg-gray-950 text-white flex items-center justify-center">
    <p class="text-gray-400 animate-pulse">Loading report...</p>
  </div>

{:else if error}
  <div class="min-h-screen bg-gray-950 text-white flex items-center justify-center">
    <div class="text-center">
      <p class="text-red-400 mb-4">{error}</p>
      <a href="/" class="text-cyan-400 hover:text-cyan-300">← Back to Upload</a>
    </div>
  </div>

{:else}
<div class="min-h-screen bg-gray-950 text-white flex flex-col">

  <!-- Top Bar -->
  <header class="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
    <div>
      <h1 class="text-lg font-bold text-cyan-400">{report.project_name}</h1>
      <p class="text-xs text-gray-500">
        {report.timestamp} · {allFunctions.length} functions · {vulnCount()} vulnerable
      </p>
    </div>
    <div class="flex gap-3">
      <a href="/history" class="text-sm text-gray-400 hover:text-cyan-400 transition-colors">← History</a>
      <a href="/" class="text-sm bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-semibold px-4 py-1.5 rounded-lg transition-colors">
        New Analysis
      </a>
    </div>
  </header>

  <div class="flex flex-1 overflow-hidden">

    <!-- Left Panel -->
    <aside class="w-72 border-r border-gray-800 flex flex-col">
      <div class="flex border-b border-gray-800 text-sm">
        {#each ['all', 'vulnerable', 'safe'] as f}
          <button
            class="flex-1 py-2 capitalize transition-colors
              {filter === f ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-500 hover:text-gray-300'}"
            on:click={() => { filter = f as typeof filter; }}
          >{f}</button>
        {/each}
      </div>

      <div class="flex-1 overflow-y-auto">
        {#each filtered as fn}
          <button
            class="w-full text-left px-4 py-3 border-b border-gray-800 hover:bg-gray-900 transition-colors
              {selected?.id === fn.id ? 'bg-gray-900 border-l-2 border-l-cyan-400' : ''}"
            on:click={() => selected = fn}
          >
            <p class="text-sm font-mono font-medium {fn.verdict === 'vulnerable' ? 'text-red-400' : 'text-green-400'}">
              {fn.function_name}
            </p>
            {#if fn.cwe}
              <p class="text-xs text-gray-500 mt-0.5">{fn.cwe}</p>
            {:else}
              <p class="text-xs text-gray-600 mt-0.5">Clean</p>
            {/if}
          </button>
        {/each}

        {#if filtered.length === 0}
          <p class="text-gray-600 text-sm text-center mt-8">No functions in this filter.</p>
        {/if}
      </div>
    </aside>

    <!-- Right Panel -->
    <main class="flex-1 p-6 overflow-y-auto">
      {#if selected}
      <div class="max-w-3xl">

        <div class="flex items-start justify-between mb-4">
          <div>
            <h2 class="text-xl font-mono font-bold">{selected.function_name}</h2>
            <p class="text-xs text-gray-500 mt-0.5">{selected.file_path} · lines {selected.start_line}–{selected.end_line}</p>
            {#if selected.verdict === 'vulnerable'}
              <p class="text-sm mt-1">
                <span class="text-red-400 font-semibold">{selected.cwe}</span>
                <span class="text-gray-400"> · {selected.cwe_name}</span>
              </p>
            {:else}
              <p class="text-sm text-green-400 mt-1">No vulnerabilities detected</p>
            {/if}
          </div>
          <div class="flex flex-col items-end gap-2">
            <span class="px-3 py-1 rounded-full text-xs font-semibold
              {selected.verdict === 'vulnerable' ? 'bg-red-900 text-red-300' : 'bg-green-900 text-green-300'}">
              {selected.verdict}
            </span>
            {#if selected.confidence !== null && selected.confidence !== undefined}
              <span class="text-xs text-gray-500">
                Confidence: {(selected.confidence * 100).toFixed(1)}%
              </span>
            {/if}
          </div>
        </div>

        <pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-sm font-mono text-gray-300 overflow-x-auto whitespace-pre-wrap">{selected.code}</pre>

        {#if selected.cwe}
          <div class="mt-4 bg-red-950 border border-red-900 rounded-xl p-4 text-sm text-red-300">
            <p class="font-semibold mb-1">⚠ {selected.cwe} — {selected.cwe_name}</p>
            <p class="text-red-400 text-xs">
              Severity: <span class="font-semibold">{selected.severity}</span> ·
              Review this function manually and apply appropriate mitigations.
            </p>
          </div>
        {/if}

      </div>
      {/if}
    </main>

  </div>
</div>
{/if}