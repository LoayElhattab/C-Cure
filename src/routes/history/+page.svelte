<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { onMount } from 'svelte';

  let history: any[] = [];
  let loading = true;
  let error = '';

  onMount(async () => {
    try {
      const raw = await invoke<string>('get_history');
      const data = JSON.parse(raw);
      if (data.error) {
        error = data.error;
      } else {
        history = data;
      }
    } catch (err) {
      error = `Failed to load history: ${err}`;
    }
    loading = false;
  });
</script>

<div class="min-h-screen bg-gray-950 text-white px-6 py-10">
  <div class="max-w-4xl mx-auto">

    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-cyan-400">Analysis History</h1>
        <p class="text-gray-500 text-sm mt-1">All past scans stored locally</p>
      </div>
      <a href="/" class="bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-semibold px-5 py-2 rounded-xl text-sm transition-colors">
        + New Analysis
      </a>
    </div>

    {#if loading}
      <p class="text-gray-500 animate-pulse">Loading history...</p>

    {:else if error}
      <p class="text-red-400">{error}</p>

    {:else if history.length === 0}
      <div class="text-center mt-20 text-gray-600">
        <p class="text-4xl mb-4">📭</p>
        <p>No analyses yet. Upload a file to get started.</p>
        <a href="/" class="mt-4 inline-block text-cyan-400 hover:text-cyan-300 text-sm">← Go to Upload</a>
      </div>

    {:else}
      <div class="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="border-b border-gray-800 text-gray-400 text-xs uppercase">
            <tr>
              <th class="text-left px-6 py-3">Project</th>
              <th class="text-left px-6 py-3">Date</th>
              <th class="text-left px-6 py-3">Functions</th>
              <th class="text-left px-6 py-3">Vulnerable</th>
              <th class="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {#each history as item}
              <tr class="border-b border-gray-800 hover:bg-gray-800 transition-colors">
                <td class="px-6 py-4 font-mono text-white">{item.project_name}</td>
                <td class="px-6 py-4 text-gray-400">{item.timestamp}</td>
                <td class="px-6 py-4 text-gray-300">{item.total_functions ?? 0}</td>
                <td class="px-6 py-4">
                  <span class="{(item.vuln_count ?? 0) > 0 ? 'text-red-400' : 'text-green-400'} font-semibold">
                    {(item.vuln_count ?? 0) > 0 ? `${item.vuln_count} found` : 'Clean'}
                  </span>
                </td>
                <td class="px-6 py-4 text-right">
                  <a href="/report/{item.id}" class="text-cyan-400 hover:text-cyan-300 transition-colors">
                    View Report →
                  </a>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

  </div>
</div>