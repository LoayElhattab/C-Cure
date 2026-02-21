<script>
  import "../app.css";
  import { page } from "$app/stores";
  import { Upload, LayoutDashboard, Clock, ShieldAlert, Eye } from 'lucide-svelte';
</script>

<div class="min-h-screen bg-gray-950 flex flex-col">

  <nav class="h-14 border-b border-gray-800 bg-gray-900 px-6 flex items-center gap-6 sticky top-0 z-50">

    <a href="/" class="flex items-center gap-2 shrink-0">
      <ShieldAlert size={18} color="#22d3ee" />
      <span class="text-white font-bold text-base">C-Cure</span>
    </a>

    <div class="w-px h-5 bg-gray-700 shrink-0"></div>

    <a href="/"
      class="flex items-center gap-2 px-3 h-8 rounded-md text-sm transition-colors
        {$page.url.pathname === '/' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}">
      <Upload size={14} />
      Upload
    </a>

    <a href="/dashboard"
      class="flex items-center gap-2 px-3 h-8 rounded-md text-sm transition-colors
        {$page.url.pathname === '/dashboard' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}">
      <LayoutDashboard size={14} />
      Dashboard
    </a>

    <a href="/history"
      class="flex items-center gap-2 px-3 h-8 rounded-md text-sm transition-colors
        {$page.url.pathname === '/history' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}">
      <Clock size={14} />
      History
    </a>

    <a href="/monitor"
      class="flex items-center gap-2 px-3 h-8 rounded-md text-sm transition-colors
        {$page.url.pathname === '/monitor' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}">
      <Eye size={14} />
      Monitor
    </a>

  </nav>

  <main class="flex-1">
    <slot />
  </main>

</div>