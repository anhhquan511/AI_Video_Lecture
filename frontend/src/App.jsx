// src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LayoutFrame from './components/LayoutFrame';
import CreateVideo from './pages/CreateVideo';
import Dashboard from './pages/Dashboard';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import VideoDetail from './pages/VideoDetail';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <LayoutFrame>
          <Routes>
            {/* 2. Thay thế dòng text cũ bằng Component Dashboard */}
            <Route path="/" element={<Dashboard />} /> 
            
            <Route path="/create" element={<CreateVideo />} />
            <Route path="/video/:id" element={<VideoDetail />} />
          </Routes>
        </LayoutFrame>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;