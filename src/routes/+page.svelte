<script lang="ts">
  import { goto } from "$app/navigation";
  import { FolderOpen, FileCode, ArrowRight } from "lucide-svelte";
  import { pendingAnalysis } from "$lib/store";

  let selectedPath: string | null = null;
  let selectedName: string = "";
  let selectionType: "file" | "folder" | null = null;
  let errorMessage = "";

  async function handleFilePick() {
    errorMessage = "";
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const result = await open({
        multiple: false,
        directory: false,
        filters: [
          { name: "C/C++ Files", extensions: ["cpp", "c", "h", "cc", "cxx"] },
        ],
      });
      if (!result) return;
      selectedPath = result as string;
      selectedName =
        selectedPath.replace(/\\/g, "/").split("/").pop() ?? selectedPath;
      selectionType = "file";
    } catch (err) {
      errorMessage = `Could not open file picker: ${err}`;
    }
  }

  async function handleFolderPick() {
    errorMessage = "";
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const result = await open({ multiple: false, directory: true });
      if (!result) return;
      selectedPath = result as string;
      selectedName =
        selectedPath.replace(/\\/g, "/").split("/").pop() ?? selectedPath;
      selectionType = "folder";
    } catch (err) {
      errorMessage = `Could not open folder picker: ${err}`;
    }
  }

  function handleAnalyze() {
    if (!selectedPath || !selectionType) return;
    pendingAnalysis.set({ type: selectionType, path: selectedPath });
    goto("/analyzing");
  }
</script>

<div
  class="min-h-screen bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white flex flex-col items-center justify-center px-6"
>
  <div class="mb-10 text-center">
    <h1
      class="text-5xl font-bold text-cyan-600 dark:text-cyan-400 tracking-tight"
    >
      C-Cure
    </h1>
    <p class="text-gray-500 dark:text-gray-400 mt-2 text-lg">
      AI-Powered C/C++ Vulnerability Detection
    </p>
  </div>

  <div
    class="w-full max-w-xl bg-white dark:bg-gray-900 rounded-2xl p-8 shadow-xl border border-gray-200 dark:border-gray-800"
  >
    <h2 class="text-xl font-semibold mb-6">Select a Target</h2>

    <!-- Two pick buttons -->
    <div class="grid grid-cols-2 gap-3 mb-6">
      <button
        on:click={handleFilePick}
        class="flex flex-col items-center justify-center gap-2 p-6 rounded-xl border-2 transition-all duration-200
          {selectionType === 'file'
          ? 'border-cyan-500 dark:border-cyan-400 bg-cyan-100 dark:bg-cyan-950 text-cyan-600 dark:text-cyan-400'
          : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-cyan-500 dark:hover:border-cyan-600 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-gray-100 dark:hover:bg-gray-800'}"
      >
        <FileCode size={28} />
        <span class="text-sm font-medium">Single File</span>
        <span class="text-xs text-gray-500 dark:text-gray-400"
          >.cpp / .c / .h</span
        >
      </button>

      <button
        on:click={handleFolderPick}
        class="flex flex-col items-center justify-center gap-2 p-6 rounded-xl border-2 transition-all duration-200
          {selectionType === 'folder'
          ? 'border-cyan-500 dark:border-cyan-400 bg-cyan-100 dark:bg-cyan-950 text-cyan-600 dark:text-cyan-400'
          : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-cyan-500 dark:hover:border-cyan-600 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-gray-100 dark:hover:bg-gray-800'}"
      >
        <FolderOpen size={28} />
        <span class="text-sm font-medium">Project Folder</span>
        <span class="text-xs text-gray-500 dark:text-gray-400"
          >Scans all C++ files</span
        >
      </button>
    </div>

    <!-- Selected indicator -->
    {#if selectedName}
      <div
        class="flex items-center gap-3 bg-gray-100 dark:bg-gray-800 rounded-xl px-4 py-3 mb-6"
      >
        {#if selectionType === "file"}
          <FileCode size={16} color="#22d3ee" />
        {:else}
          <FolderOpen size={16} color="#22d3ee" />
        {/if}
        <div class="flex-1 min-w-0">
          <p
            class="text-cyan-600 dark:text-cyan-400 text-sm font-medium truncate"
          >
            {selectedName}
          </p>
          <p class="text-gray-500 dark:text-gray-400 text-xs">{selectedPath}</p>
        </div>
      </div>
    {/if}

    {#if errorMessage}
      <p class="text-red-500 dark:text-red-400 text-sm mb-4">{errorMessage}</p>
    {/if}

    <!-- Analyze Button -->
    <button
      disabled={!selectedPath}
      on:click={handleAnalyze}
      class="w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2
        {selectedPath
        ? 'bg-cyan-500 hover:bg-cyan-600 dark:hover:bg-cyan-400 text-white dark:text-gray-950 cursor-pointer'
        : 'bg-gray-200 dark:bg-gray-800 text-gray-500 dark:text-gray-600 cursor-not-allowed'}"
    >
      Run Analysis
      <ArrowRight size={15} />
    </button>
  </div>

  <p class="mt-8 text-gray-500 dark:text-gray-400 text-sm">
    <a
      href="/history"
      class="hover:text-cyan-500 dark:hover:text-cyan-400 transition-colors"
      >View past analyses →</a
    >
  </p>
</div>
