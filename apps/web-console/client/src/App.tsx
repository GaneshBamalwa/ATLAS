import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import ArchitecturePage from "./pages/ArchitecturePage";
import ToolsPage from "./pages/ToolsPage";
import SettingsPage from "./pages/SettingsPage";
import ExecutionGraphPage from "./pages/ExecutionGraphPage";
import IntegrationsPage from "./pages/IntegrationsPage";


import ConsoleLayout from "./components/ConsoleLayout";

function Router() {
  return (
    <ConsoleLayout>
      <Switch>
        <Route path={"/"} />
        <Route path={"/architecture"} component={ArchitecturePage} />
        <Route path={"/graph"} component={ExecutionGraphPage} />
        <Route path={"/graph/:id"} component={ExecutionGraphPage} />
        <Route path={"/tools"} component={ToolsPage} />
        <Route path={"/integrations"} component={IntegrationsPage} />
        <Route path={"/settings"} component={SettingsPage} />
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
  return (
    <ErrorBoundary>
      <ThemeProvider
        defaultTheme="dark"
        // switchable
      >
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
