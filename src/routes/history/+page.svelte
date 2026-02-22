<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import { Trash2, X } from "lucide-svelte";
  import { success, error as errorToast } from "$lib/toast";

  let history: any[] = [];
  let loading = true;
  let deleting: Record<number, boolean> = {};
  let searchTerm = "";

  $: filteredHistory = history.filter((item) =>
    item.project_name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  onMount(async () => {
    await loadHistory();
  });

  async function loadHistory() {
    loading = true;
    try {
      const raw = await invoke<string>("get_history");
      const data = JSON.parse(raw);
      if (data.error) {
        errorToast(data.error);
      } else {
        history = data;
      }
    } catch (err) {
      errorToast(`Failed to load history: ${err}`);
    }
    loading = false;
  }

  async function handleDelete(id: number, name: string) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    deleting[id] = true;
    deleting = deleting;
    try {
      await invoke("delete_analysis", { analysisId: id });
      history = history.filter((h) => h.id !== id);
      success(`"${name}" deleted.`);
    } catch (err) {
      errorToast(`Failed to delete: ${err}`);
    }
    deleting[id] = false;
    deleting = deleting;
  }
</script>

<div
  class="min-h-screen bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white px-6 py-10"
>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-cyan-600 dark:text-cyan-400">
          Analysis History
        </h1>
        <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">
          All past scans stored locally
        </p>
      </div>
      <a
        href="/"
        class="bg-cyan-500 hover:bg-cyan-600 dark:hover:bg-cyan-400 text-gray-900 dark:text-gray-950 font-semibold px-5 py-2 rounded-xl text-sm transition-colors"
      >
        + New Analysis
      </a>
    </div>

    {#if !loading && history.length > 0}
      <div
        class="mb-6 flex items-center bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl px-4 py-2"
      >
        <input
          type="text"
          bind:value={searchTerm}
          placeholder="Search by project name..."
          class="flex-1 bg-transparent border-none outline-none text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
        />
        {#if searchTerm.length > 0}
          <button
            on:click={() => (searchTerm = "")}
            class="ml-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            title="Clear search"
          >
            <X size={16} />
          </button>
        {/if}
      </div>
    {/if}

    {#if loading}
      <div
        class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden"
      >
        <table class="w-full text-sm">
          <thead
            class="border-b border-gray-200 dark:border-gray-800 text-gray-500 dark:text-gray-400 text-xs uppercase"
          >
            <tr>
              <th class="text-left px-6 py-3">Project</th>
              <th class="text-left px-6 py-3">Date</th>
              <th class="text-left px-6 py-3">Functions</th>
              <th class="text-left px-6 py-3">Vulnerable</th>
              <th class="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {#each Array(4) as _}
              <tr class="border-b border-gray-200 dark:border-gray-800">
                <td class="px-6 py-4">
                  <div
                    class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 animate-pulse"
                  ></div>
                </td>
                <td class="px-6 py-4">
                  <div
                    class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 animate-pulse"
                  ></div>
                </td>
                <td class="px-6 py-4">
                  <div
                    class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 animate-pulse"
                  ></div>
                </td>
                <td class="px-6 py-4">
                  <div
                    class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 animate-pulse"
                  ></div>
                </td>
                <td class="px-6 py-4">
                  <div class="flex justify-end gap-3">
                    <div
                      class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse"
                    ></div>
                    <div
                      class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4 animate-pulse"
                    ></div>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else if history.length === 0}
      <div class="text-center mt-20 text-gray-500 dark:text-gray-400">
        <p class="text-4xl mb-4">📭</p>
        <p>No analyses yet. Upload a file to get started.</p>
        <a
          href="/"
          class="mt-4 inline-block text-cyan-500 dark:text-cyan-400 hover:text-cyan-600 dark:hover:text-cyan-300 text-sm"
          >← Go to Upload</a
        >
      </div>
    {:else if filteredHistory.length === 0}
      <div class="text-center mt-20 text-gray-500 dark:text-gray-400">
        <p class="text-4xl mb-4">🔍</p>
        <p>No matching analyses found.</p>
        <button
          on:click={() => (searchTerm = "")}
          class="mt-4 inline-block text-cyan-500 dark:text-cyan-400 hover:text-cyan-600 dark:hover:text-cyan-300 text-sm"
        >
          Clear filter
        </button>
      </div>
    {:else}
      <div
        class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden"
      >
        <table class="w-full text-sm">
          <thead
            class="border-b border-gray-200 dark:border-gray-800 text-gray-500 dark:text-gray-400 text-xs uppercase"
          >
            <tr>
              <th class="text-left px-6 py-3">Project</th>
              <th class="text-left px-6 py-3">Date</th>
              <th class="text-left px-6 py-3">Functions</th>
              <th class="text-left px-6 py-3">Vulnerable</th>
              <th class="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {#each filteredHistory as item}
              <tr
                class="border-b border-gray-200 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <td class="px-6 py-4 font-mono">{item.project_name}</td>
                <td class="px-6 py-4 text-gray-500 dark:text-gray-400"
                  >{item.timestamp}</td
                >
                <td class="px-6 py-4 text-gray-700 dark:text-gray-300"
                  >{item.total_functions ?? 0}</td
                >
                <td class="px-6 py-4">
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
                <td class="px-6 py-4">
                  <div class="flex items-center justify-end gap-3">
                    <a
                      href="/report/{item.id}"
                      class="text-cyan-500 dark:text-cyan-400 hover:text-cyan-600 dark:hover:text-cyan-300 transition-colors"
                    >
                      View →
                    </a>
                    <button
                      on:click={() => handleDelete(item.id, item.project_name)}
                      disabled={deleting[item.id]}
                      class="text-gray-500 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                      title="Delete analysis"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>
