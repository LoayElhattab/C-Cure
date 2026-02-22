<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import {
    FolderOpen,
    RefreshCw,
    Trash2,
    AlertTriangle,
    CheckCircle,
  } from "lucide-svelte";

  let projects: any[] = [];
  let loading = true;
  let error = "";
  let checkResults: Record<number, any> = {};
  let checking: Record<number, boolean> = {};
  let refreshing: Record<number, boolean> = {};

  onMount(async () => {
    await loadProjects();
  });

  async function loadProjects() {
    loading = true;
    try {
      const raw = await invoke<string>("monitor_list");
      projects = JSON.parse(raw);
    } catch (err) {
      error = `Failed to load projects: ${err}`;
    }
    loading = false;
  }

  async function handleRegister() {
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const folder = await open({ directory: true, multiple: false });
      if (!folder) return;
      const raw = await invoke<string>("monitor_register", {
        folderPath: folder as string,
      });
      const result = JSON.parse(raw);
      if (result.error) {
        error = result.error;
        return;
      }
      await loadProjects();
    } catch (err) {
      error = `Failed to register project: ${err}`;
    }
  }

  async function handleCheck(projectId: number) {
    checking[projectId] = true;
    checking = checking;
    try {
      const raw = await invoke<string>("monitor_check", { projectId });
      checkResults[projectId] = JSON.parse(raw);
      checkResults = checkResults;
    } catch (err) {
      error = `Failed to check changes: ${err}`;
    }
    checking[projectId] = false;
    checking = checking;
  }

  async function handleRefresh(projectId: number) {
    refreshing[projectId] = true;
    refreshing = refreshing;
    try {
      await invoke<string>("monitor_refresh", { projectId });
      delete checkResults[projectId];
      checkResults = checkResults;
    } catch (err) {
      error = `Failed to refresh: ${err}`;
    }
    refreshing[projectId] = false;
    refreshing = refreshing;
  }

  async function handleRemove(projectId: number) {
    try {
      await invoke<string>("monitor_remove", { projectId });
      delete checkResults[projectId];
      await loadProjects();
    } catch (err) {
      error = `Failed to remove: ${err}`;
    }
  }
</script>

<div
  class="bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white px-6 py-8 min-h-screen"
>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold">File Monitor</h1>
        <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">
          Track changes in your C++ projects
        </p>
      </div>
      <button
        on:click={handleRegister}
        class="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-600 dark:hover:bg-cyan-400 text-gray-900 dark:text-gray-950 font-semibold px-4 py-2 rounded-xl text-sm transition-colors"
      >
        <FolderOpen size={15} />
        Watch Folder
      </button>
    </div>

    {#if error}
      <p class="text-red-500 dark:text-red-400 text-sm mb-4">{error}</p>
    {/if}

    {#if loading}
      <p class="text-gray-500 dark:text-gray-400 animate-pulse">Loading...</p>
    {:else if projects.length === 0}
      <div class="text-center mt-20 text-gray-500 dark:text-gray-400">
        <p class="text-4xl mb-4">👁</p>
        <p>No folders being watched yet.</p>
        <p class="text-sm mt-1">
          Click "Watch Folder" to start monitoring a C++ project.
        </p>
      </div>
    {:else}
      <div class="space-y-4">
        {#each projects as project}
          <div
            class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5"
          >
            <!-- Project Header -->
            <div class="flex items-start justify-between mb-4">
              <div>
                <p class="font-semibold">{project.name}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {project.folder_path}
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Registered: {project.registered_at}
                </p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  on:click={() => handleCheck(project.id)}
                  disabled={checking[project.id]}
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors disabled:opacity-50"
                >
                  <AlertTriangle size={12} />
                  {checking[project.id] ? "Checking..." : "Check Changes"}
                </button>
                <button
                  on:click={() => handleRefresh(project.id)}
                  disabled={refreshing[project.id]}
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors disabled:opacity-50"
                  title="Update baseline hashes"
                >
                  <RefreshCw size={12} />
                  {refreshing[project.id] ? "Updating..." : "Update Baseline"}
                </button>
                <button
                  on:click={() => handleRemove(project.id)}
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 hover:bg-red-100 dark:hover:bg-red-900 text-gray-500 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>

            <!-- Change Results -->
            {#if checkResults[project.id]}
              {@const result = checkResults[project.id]}

              {#if result.total_changes === 0 && result.deleted.length === 0}
                <div
                  class="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm bg-green-100 dark:bg-green-950 border border-green-200 dark:border-green-900 rounded-lg px-4 py-3"
                >
                  <CheckCircle size={14} />
                  No changes detected since last baseline.
                </div>
              {:else}
                <div class="space-y-3">
                  {#if result.changed.length > 0}
                    <div>
                      <p
                        class="text-xs font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wide mb-2"
                      >
                        Modified ({result.changed.length})
                      </p>
                      {#each result.changed as file}
                        <div
                          class="flex items-center justify-between py-1.5 px-3 bg-orange-100 dark:bg-orange-950 border border-orange-200 dark:border-orange-900 rounded-lg mb-1"
                        >
                          <p
                            class="text-xs font-mono text-orange-600 dark:text-orange-300"
                          >
                            {file.replace(/\\/g, "/").split("/").pop()}
                          </p>
                          <a
                            href="/"
                            on:click|preventDefault={() => {
                              const { pendingAnalysis } = import(
                                "$lib/store"
                              ).then((m) => {
                                m.pendingAnalysis.set({
                                  type: "file",
                                  path: file,
                                });
                                window.location.href = "/analyzing";
                              });
                            }}
                            class="text-xs text-cyan-500 dark:text-cyan-400 hover:text-cyan-600 dark:hover:text-cyan-300"
                          >
                            Re-analyze →
                          </a>
                        </div>
                      {/each}
                    </div>
                  {/if}

                  {#if result.added.length > 0}
                    <div>
                      <p
                        class="text-xs font-semibold text-cyan-600 dark:text-cyan-400 uppercase tracking-wide mb-2"
                      >
                        New Files ({result.added.length})
                      </p>
                      {#each result.added as file}
                        <div
                          class="py-1.5 px-3 bg-gray-100 dark:bg-gray-800 rounded-lg mb-1"
                        >
                          <p
                            class="text-xs font-mono text-cyan-600 dark:text-cyan-300"
                          >
                            {file.replace(/\\/g, "/").split("/").pop()}
                          </p>
                        </div>
                      {/each}
                    </div>
                  {/if}

                  {#if result.deleted.length > 0}
                    <div>
                      <p
                        class="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide mb-2"
                      >
                        Deleted ({result.deleted.length})
                      </p>
                      {#each result.deleted as file}
                        <div
                          class="py-1.5 px-3 bg-red-100 dark:bg-red-950 border border-red-200 dark:border-red-900 rounded-lg mb-1"
                        >
                          <p
                            class="text-xs font-mono text-red-600 dark:text-red-300"
                          >
                            {file.replace(/\\/g, "/").split("/").pop()}
                          </p>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              {/if}
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
