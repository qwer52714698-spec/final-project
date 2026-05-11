import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import SectorNews from './pages/SectorNews'
import SectorStocks from './pages/SectorStocks'
import AllNews from './pages/AllNews'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/news" element={<AllNews />} />
            <Route path="/sector/:sectorId/news" element={<SectorNews />} />
            <Route path="/sector/:sectorId/stocks" element={<SectorStocks />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
