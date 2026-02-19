<script lang="ts">
  import { goto } from '$app/navigation';
  import { invoke } from '@tauri-apps/api/core';
  import { open } from '@tauri-apps/plugin-shell';

  let isDragging = false;
  let selectedFile: string | null = null;
  let selectedFileName: string = '';
  let errorMessage = '';
  let isAnalyzing = false;

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragLeave() {
    isDragging = false;
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
    const file = e.dataTransfer?.files[0];
    if (file) validateAndSet(file);
  }

  function handleFileInput(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) validateAndSet(file);
  }

  function validateAndSet(file: File) {
    if (!file.name.endsWith('.cpp') && !file.name.endsWith('.h') && !file.name.endsWith('.c')) {
      errorMessage = 'Only .cpp, .c, or .h files are supported.';
      selectedFile = null;
      return;
    }
    errorMessage = '';
    selectedFileName = file.name;
    // @ts-ignore — webkitRelativePath / path is available in Tauri's webview
    selectedFile = file.path ?? file.name;
  }

  async function handleAnalyze() {
    if (!selectedFile) return;
    isAnalyzing = true;
    errorMessage = '';

    try {
      const raw = await invoke<string>('analyze_file', { filePath: selectedFile });
      const result = JSON.parse(raw);

      if (result.error) {
        errorMessage = result.error;
        isAnalyzing = false;
        return;
      }

      goto(`/report/${result.analysis_id}`);
    } catch (err) {
      errorMessage = `Unexpected error: ${err}`;
      isAnalyzing = false;
    }
  }

  async function handleFolderAnalyze() {
    errorMessage = '';
    isAnalyzing = true;

    try {
      // Tauri folder picker
      const { dialog } = await import('@tauri-apps/plugin-dialog');
      const folder = await dialog.open({ directory: true, multiple: false });

      if (!folder) {
        isAnalyzing = false;
        return;
      }

      const raw = await invoke<string>('analyze_folder', { folderPath: folder as string });
      const result = JSON.parse(raw);

      if (result.error) {
        errorMessage = result.error;
        isAnalyzing = false;
        return;
      }

      goto(`/report/${result.analysis_id}`);
    } catch (err) {
      errorMessage = `Unexpected error: ${err}`;
      isAnalyzing = false;
    }
  }
</script>

<div class="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center px-6">

  <div class="mb-10 text-center">
    <h1 class="text-5xl font-bold text-cyan-400 tracking-tight">C-Cure</h1>
    <p class="text-gray-400 mt-2 text-lg">AI-Powered C/C++ Vulnerability Detection</p>
  </div>

  <div class="w-full max-w-xl bg-gray-900 rounded-2xl p-8 shadow-xl border border-gray-800">

    <h2 class="text-xl font-semibold mb-6 text-gray-100">Upload a File</h2>

    <div
      role="button"
      tabindex="0"
      class="border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200
        {isDragging ? 'border-cyan-400 bg-cyan-950' : 'border-gray-700 hover:border-cyan-600 hover:bg-gray-800'}"
      on:dragover={handleDragOver}
      on:dragleave={handleDragLeave}
      on:drop={handleDrop}
      on:click={() => document.getElementById('fileInput')?.click()}
      on:keydown={(e) => e.key === 'Enter' && document.getElementById('fileInput')?.click()}
    >
      <div class="text-4xl mb-3">📂</div>
      {#if selectedFileName}
        <p class="text-cyan-400 font-medium">{selectedFileName}</p>
        <p class="text-gray-500 text-sm mt-1">Ready to analyze</p>
      {:else}
        <p class="text-gray-400">Drag & drop a <span class="text-cyan-400">.cpp</span> file here</p>
        <p class="text-gray-600 text-sm mt-1">or click to browse</p>
      {/if}
    </div>

    <input
      id="fileInput"
      type="file"
      accept=".cpp,.c,.h"
      class="hidden"
      on:change={handleFileInput}
    />

    {#if errorMessage}
      <p class="text-red-400 text-sm mt-3">{errorMessage}</p>
    {/if}

    <div class="flex items-center my-6 gap-3">
      <div class="flex-1 h-px bg-gray-800"></div>
      <span class="text-gray-600 text-sm">or</span>
      <div class="flex-1 h-px bg-gray-800"></div>
    </div>

    <button
      class="w-full py-3 rounded-xl border border-gray-700 text-gray-400 hover:border-cyan-600 hover:text-cyan-400 transition-all duration-200 text-sm disabled:opacity-50"
      disabled={isAnalyzing}
      on:click={handleFolderAnalyze}
    >
      📁 Upload Project Folder
    </button>

    <button
      disabled={!selectedFile || isAnalyzing}
      on:click={handleAnalyze}
      class="mt-4 w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200
        {selectedFile && !isAnalyzing
          ? 'bg-cyan-500 hover:bg-cyan-400 text-gray-950 cursor-pointer'
          : 'bg-gray-800 text-gray-600 cursor-not-allowed'}"
    >
      {isAnalyzing ? 'Analyzing...' : 'Run Analysis →'}
    </button>

  </div>

  <p class="mt-8 text-gray-600 text-sm">
    <a href="/history" class="hover:text-cyan-400 transition-colors">View past analyses →</a>
  </p>

</div>