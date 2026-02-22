<script lang="ts">
    import { invoke } from "@tauri-apps/api/core";
    import { onMount } from "svelte";
    import { theme } from "$lib/theme";
    import { success, error as errorToast } from "$lib/toast";
    import { Sun, Moon, Wifi } from "lucide-svelte";

    let kaggleUrl = "";
    let saving = false;
    let loading = true;

    onMount(async () => {
        try {
            const raw = await invoke<string>("get_settings");
            const data = JSON.parse(raw);
            kaggleUrl = data.kaggle_url ?? "";
        } catch (err) {
            errorToast(`Failed to load settings: ${err}`);
        }
        loading = false;
    });

    async function handleSave() {
        saving = true;
        try {
            await invoke("save_settings", { kaggleUrl });
            success("Settings saved successfully.");
        } catch (err) {
            errorToast(`Failed to save settings: ${err}`);
        }
        saving = false;
    }

    function toggleTheme() {
        console.log("toggleTheme called — current value:", $theme); // ← debug
        theme.update((t) => (t === "dark" ? "light" : "dark"));
    }
</script>

<div
    class="min-h-screen px-6 py-10 bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white"
>
    <div class="max-w-2xl mx-auto">
        <div class="mb-8">
            <h1 class="text-2xl font-bold">Settings</h1>
            <p class="text-sm mt-1 text-gray-500 dark:text-gray-400">
                Configure C-Cure preferences
            </p>
        </div>

        {#if loading}
            <div class="animate-pulse text-gray-500 dark:text-gray-400">
                Loading...
            </div>
        {:else}
            <!-- Theme -->
            <div
                class="rounded-xl border p-6 mb-4 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800"
            >
                <h2
                    class="text-sm font-semibold uppercase tracking-wide mb-1 text-gray-500 dark:text-gray-400"
                >
                    Appearance
                </h2>
                <p class="text-sm mb-4 text-gray-500 dark:text-gray-400">
                    Choose between dark and light mode.
                </p>
                <button
                    on:click={toggleTheme}
                    class="flex items-center gap-3 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 hover:border-cyan-500 transition-colors text-gray-700 dark:text-gray-300 hover:text-cyan-600 dark:hover:text-cyan-400"
                >
                    {#if $theme === "dark"}
                        <Moon size={16} />
                        <span class="text-sm font-medium">Dark Mode</span>
                        <span
                            class="ml-2 text-xs text-gray-500 dark:text-gray-400"
                            >Click to switch to Light</span
                        >
                    {:else}
                        <Sun size={16} />
                        <span class="text-sm font-medium">Light Mode</span>
                        <span
                            class="ml-2 text-xs text-gray-500 dark:text-gray-400"
                            >Click to switch to Dark</span
                        >
                    {/if}
                </button>
            </div>

            <!-- Kaggle URL -->
            <div
                class="rounded-xl border p-6 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800"
            >
                <h2
                    class="text-sm font-semibold uppercase tracking-wide mb-1 text-gray-500 dark:text-gray-400"
                >
                    Kaggle API
                </h2>
                <p class="text-sm mb-4 text-gray-500 dark:text-gray-400">
                    Paste your ngrok URL from the running Kaggle notebook.
                </p>
                <div class="flex gap-3">
                    <div
                        class="flex-1 flex items-center gap-2 rounded-lg border px-3 py-1 bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700"
                    >
                        <Wifi
                            size={14}
                            class="text-gray-400 dark:text-gray-500"
                        />
                        <input
                            type="text"
                            bind:value={kaggleUrl}
                            placeholder="https://xxxx.ngrok-free.app"
                            class="flex-1 bg-transparent py-2.5 text-sm outline-none text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                        />
                    </div>
                    <button
                        on:click={handleSave}
                        disabled={saving}
                        class="px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-cyan-500 hover:bg-cyan-600 text-white disabled:opacity-50"
                    >
                        {saving ? "Saving..." : "Save"}
                    </button>
                </div>
            </div>
        {/if}
    </div>
</div>
