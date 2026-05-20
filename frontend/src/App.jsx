import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import SectorNews from './pages/SectorNews'
import SectorStocks from './pages/SectorStocks'
import AllNews from './pages/AllNews'
import Login from './pages/Login'
import Signup from './pages/Signup'
import StockNewsDetail from './pages/StockNewsDetail'
import MyPage from './pages/MyPage' // ✅ 마이페이지 추가

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
            <Route path="/stock/:symbol/news" element={<StockNewsDetail />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/mypage" element={<MyPage />} /> {/* ✅ 마이페이지 라우터 추가 */}
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
