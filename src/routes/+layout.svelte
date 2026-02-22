<script>
  import "../app.css";
  import { page } from "$app/stores";
  import {
    Upload,
    LayoutDashboard,
    Clock,
    ShieldAlert,
    Eye,
    Settings,
  } from "lucide-svelte";
  import { toasts } from "$lib/toast";
  import { theme } from "$lib/theme";
</script>

<div
  class="min-h-screen flex flex-col bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-white"
>
  <nav
    class="h-14 border-b px-6 flex items-center gap-6 sticky top-0 z-50
           bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-800"
  >
    <a href="/" class="flex items-center gap-2 shrink-0">
      <ShieldAlert size={18} color="#22d3ee" />
      <span class="font-bold text-base">C-Cure</span>
    </a>

    <div class="w-px h-5 bg-gray-300 dark:bg-gray-700 shrink-0"></div>

    {#each [{ href: "/", label: "Upload", icon: Upload }, { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard }, { href: "/history", label: "History", icon: Clock }, { href: "/monitor", label: "Monitor", icon: Eye }] as link (link.href)}
      <a
        href={link.href}
        class="flex items-center gap-2 px-3 h-8 rounded-md text-sm transition-colors
          {$page.url.pathname === link.href
          ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
          : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-800'}"
      >
        <svelte:component this={link.icon} size={14} />
        {link.label}
      </a>
    {/each}

    <div class="flex-1"></div>

    <a
      href="/settings"
      class="flex items-center gap-2 px-3 h-8 rounded-md text-sm transition-colors
        {$page.url.pathname === '/settings'
        ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
        : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-800'}"
    >
      <Settings size={14} />
      Settings
    </a>
  </nav>

  <main class="flex-1">
    <slot />
  </main>

  <!-- Toast Container -->
  <div
    class="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none"
  >
    {#each $toasts as t (t.id)}
      <div
        class="pointer-events-auto px-4 py-3 rounded-xl text-sm font-medium shadow-lg
               flex items-center gap-3 min-w-[260px] max-w-sm
               {t.type === 'success'
          ? 'bg-green-100 dark:bg-green-900 border border-green-300 dark:border-green-700 text-green-800 dark:text-green-200'
          : t.type === 'error'
            ? 'bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 text-red-800 dark:text-red-200'
            : 'bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200'}"
      >
        <span>
          {t.type === "success" ? "✓" : t.type === "error" ? "✕" : "ℹ"}
        </span>
        {t.message}
      </div>
    {/each}
  </div>
</div>
