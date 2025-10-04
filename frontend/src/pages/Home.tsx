import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Home.css';

const Home: React.FC = () => {
  const navigate = useNavigate();

  const handleStartRedesign = () => {
    navigate('/ai-assistant');
  };

  return (
    <div className="home-page">
      <div className="hero-section">
        <h1 className="hero-title">🌱 GreenMorph 智能改造系统</h1>
        <p className="hero-subtitle">
          AI智能旧物改造，让环保变得简单有趣，为地球贡献一份力量
        </p>
        
        <div className="hero-features">
          <div className="feature-item">
            <div className="feature-icon">📸</div>
            <h3>上传旧物</h3>
            <p>支持多种格式的旧物照片上传</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">🎨</div>
            <h3>AI智能改造</h3>
            <p>AI生成详细的改造方案和效果图</p>
          </div>
          <div className="feature-item">
            <div className="feature-icon">🌱</div>
            <h3>环保理念</h3>
            <p>专业评分、材料清单与环保建议</p>
          </div>
        </div>
        
        <div className="hero-actions">
          <button 
            className="cta-button"
            onClick={handleStartRedesign}
          >
            开始智能改造
          </button>
        </div>
        
        <div className="welcome-message">
          <p>让每一件旧物都焕发新的生命 ✨</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
