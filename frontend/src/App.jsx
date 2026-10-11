import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import CreateJob from "./pages/CreateJob";
import JobList from "./pages/JobList";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="layout">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/create" element={<CreateJob />} />
              <Route path="/jobs" element={<JobList />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#ffffff",
            color: "#111827",
            border: "1px solid #e2e6ef",
            boxShadow: "0 4px 12px rgba(0,0,0,.08)",
            fontSize: "13.5px",
            borderRadius: "8px",
          },
          success: { iconTheme: { primary: "#059669", secondary: "#fff" } },
          error:   { iconTheme: { primary: "#dc2626", secondary: "#fff" } },
        }}
      />
    </QueryClientProvider>
  );
}
