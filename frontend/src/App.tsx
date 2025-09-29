import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import AIAssistant from './pages/AIAssistant';
import Community from './pages/Community';
import Profile from './pages/Profile';
import About from './pages/About';
import './App.css';
import './styles/global.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/ai-assistant" element={<AIAssistant />} />
          <Route path="/community" element={<Community />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;