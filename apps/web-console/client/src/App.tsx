import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useEffect } from "react";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ChatProvider } from "./contexts/ChatContext";
import Home from "./pages/Home";
import ArchitecturePage from "./pages/ArchitecturePage";
import ToolsPage from "./pages/ToolsPage";
import SettingsPage from "./pages/SettingsPage";
import ExecutionGraphPage from "./pages/ExecutionGraphPage";
import IntegrationsPage from "./pages/IntegrationsPage";
import MarkdownDebugPage from "./pages/MarkdownDebugPage";
import { syncUserIdFromUrl } from "./lib/authUser";


import ConsoleLayout from "./components/ConsoleLayout";

function Router() {
  return (
    <ConsoleLayout>
      <Switch>
        <Route path={"/"} component={Home} />
        <Route path={"/architecture"} component={ArchitecturePage} />
        <Route path={"/graph"} component={ExecutionGraphPage} />
        <Route path={"/graph/:id"} component={ExecutionGraphPage} />
        <Route path={"/tools"} component={ToolsPage} />
        <Route path={"/integrations"} component={IntegrationsPage} />
        <Route path={"/settings"} component={SettingsPage} />
        <Route path={"/debug/markdown"} component={MarkdownDebugPage} />
        <Route path={"/404"} component={NotFound} />
        {/* Final fallback route */}
        <Route component={NotFound} />
      </Switch>
    </ConsoleLayout>
  );
}

// NOTE: About Theme
// - First choose a default theme according to your design style (dark or light bg), than change color palette in index.css
//   to keep consistent foreground/background color across components
// - If you want to make theme switchable, pass `switchable` ThemeProvider and use `useTheme` hook

function App() {
  useEffect(() => {
    syncUserIdFromUrl();
  }, []);

  return (
    <ErrorBoundary>
      <ThemeProvider
        defaultTheme="dark"
        // switchable
      >
        <ChatProvider>
          <TooltipProvider>
            <Toaster />
            <Router />
          </TooltipProvider>
        </ChatProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
