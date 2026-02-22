<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { pendingAnalysis } from "$lib/store";
  import { get } from "svelte/store";

  const steps = [
    "Reading source file...",
    "Extracting functions with tree-sitter...",
    "Running triage model...",
    "Classifying vulnerabilities...",
    "Generating report...",
  ];

  let currentStep = 0;
  let progress = 0;
  let errorMessage = "";

  function setStep(i: number) {
    currentStep = i;
    progress = Math.round((i / (steps.length - 1)) * 100);
  }

  onMount(async () => {
    const pending = get(pendingAnalysis);
    if (!pending) {
      goto("/");
      return;
    }

    try {
      // Step 0 — Reading source file
      setStep(0);
      await tick();

      // Step 1 — Extract functions
      setStep(1);
      const extractRaw = await invoke<string>("extract_functions", {
        filePath: pending.path,
      });
      const extracted = JSON.parse(extractRaw);
      if (extracted.error) {
        errorMessage = extracted.error;
        return;
      }
      if (extracted.count === 0) {
        errorMessage = "No functions found in file.";
        return;
      }

      // Step 2 — Check API / triage
      setStep(2);
      const apiRaw = await invoke<string>("check_api");
      const apiStatus = JSON.parse(apiRaw);
      if (!apiStatus.reachable) {
        errorMessage =
          "Kaggle API is unreachable. Make sure the notebook is running and the URL is set.";
        return;
      }

      // Step 3 — Full analysis (triage + classify)
      setStep(3);
      let raw: string;
      if (pending.type === "file") {
        raw = await invoke<string>("analyze_file", { filePath: pending.path });
      } else {
        raw = await invoke<string>("analyze_folder", {
          folderPath: pending.path,
        });
      }
      const result = JSON.parse(raw);
      if (result.error) {
        errorMessage = result.error;
        return;
      }

      // Step 4 — Done
      setStep(4);
      pendingAnalysis.set(null);
      setTimeout(() => goto(`/report/${result.analysis_id}`), 600);
    } catch (err) {
      errorMessage = `Unexpected error: ${err}`;
    }
  });

  // needed to let Svelte re-render between steps
  function tick() {
    return new Promise((resolve) => setTimeout(resolve, 300));
  }
</script>

<div
  class="min-h-screen bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white flex flex-col items-center justify-center px-6"
>
  <h1 class="text-3xl font-bold text-cyan-600 dark:text-cyan-400 mb-2">
    Analyzing...
  </h1>
  <p class="text-gray-500 dark:text-gray-400 mb-10">
    Please wait while C-Cure scans your code.
  </p>

  <div
    class="w-full max-w-md bg-gray-200 dark:bg-gray-800 rounded-full h-2 mb-6"
  >
    <div
      class="bg-cyan-500 dark:bg-cyan-400 h-2 rounded-full transition-all duration-500"
      style="width: {progress}%"
    ></div>
  </div>

  <div class="w-full max-w-md space-y-3">
    {#each steps as step, i}
      <div
        class="flex items-center gap-3 text-sm
        {i < currentStep
          ? 'text-cyan-600 dark:text-cyan-400'
          : i === currentStep
            ? ''
            : 'text-gray-400 dark:text-gray-500'}"
      >
        <span class="w-4 text-center shrink-0">
          {#if i < currentStep}✓{:else if i === currentStep}⟳{:else}○{/if}
        </span>
        {step}
      </div>
    {/each}
  </div>

  {#if errorMessage}
    <div
      class="mt-8 w-full max-w-md bg-red-100 dark:bg-red-950 border border-red-200 dark:border-red-900 rounded-xl p-4 text-sm text-red-600 dark:text-red-300"
    >
      <p class="font-semibold mb-1">Analysis failed</p>
      <p>{errorMessage}</p>
      <a
        href="/"
        class="mt-3 inline-block text-cyan-500 dark:text-cyan-400 hover:text-cyan-600 dark:hover:text-cyan-300"
        >← Try again</a
      >
    </div>
  {/if}
</div>
