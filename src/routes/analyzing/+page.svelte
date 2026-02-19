<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  const steps = [
    'Reading source file...',
    'Extracting functions with tree-sitter...',
    'Running triage model...',
    'Classifying vulnerabilities...',
    'Generating report...',
  ];

  let currentStep = 0;
  let progress = 0;

  onMount(() => {
    const interval = setInterval(() => {
      if (currentStep < steps.length - 1) {
        currentStep++;
        progress = Math.round((currentStep / (steps.length - 1)) * 100);
      } else {
        clearInterval(interval);
        setTimeout(() => goto('/report/1'), 800);
      }
    }, 1000);

    return () => clearInterval(interval);
  });
</script>

<div class="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center px-6">

  <h1 class="text-3xl font-bold text-cyan-400 mb-2">Analyzing...</h1>
  <p class="text-gray-400 mb-10">Please wait while C-Cure scans your code.</p>

  <!-- Progress Bar -->
  <div class="w-full max-w-md bg-gray-800 rounded-full h-2 mb-6">
    <div
      class="bg-cyan-400 h-2 rounded-full transition-all duration-700"
      style="width: {progress}%"
    ></div>
  </div>

  <!-- Current Step -->
  <div class="w-full max-w-md space-y-2">
    {#each steps as step, i}
      <div class="flex items-center gap-3 text-sm {i < currentStep ? 'text-cyan-400' : i === currentStep ? 'text-white' : 'text-gray-700'}">
        <span>
          {#if i < currentStep}✓{:else if i === currentStep}⟳{:else}○{/if}
        </span>
        {step}
      </div>
    {/each}
  </div>

</div>