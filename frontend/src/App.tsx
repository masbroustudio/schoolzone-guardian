import React, { useState, useEffect, useRef } from 'react';
import { Sun, Moon, LogOut, User } from 'lucide-react';

interface School {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  zone_radius: number;
  historical_incidents: number;
  double_parking_factor: number;
  base_risk: number;
}

interface RiskSlot {
  time_window: string;
  score: number;
  level: string;
  weather_multiplier: number;
  factors: string[];
  risk_breakdown?: { factor: string; weight: number; contribution: number }[];
}

interface VolunteerShift {
  roster_id: number;
  school_id: string;
  volunteer_name: string;
  assigned_zone: string;
  time_window: string;
  shift_date: string;
  status: string;
}

interface Hazard {
  hazard_id: number;
  school_id: string;
  description: string;
  severity_multiplier: number;
  hazard_type: string;
  created_at?: string;
}

interface ChatBubble {
  sender: 'user' | 'bot';
  text: string;
  grounded?: boolean;
}

const FALLBACK_SCHOOLS: School[] = [
  {
    id: "school_1",
    name: "PS 199 Jessie Isador Straus (Manhattan)",
    address: "270 W 70th St, New York, NY 10023",
    latitude: 40.7782,
    longitude: -73.9856,
    zone_radius: 300,
    historical_incidents: 14,
    double_parking_factor: 1.35,
    base_risk: 42.0
  },
  {
    id: "school_2",
    name: "Stuyvesant High School (Battery Park)",
    address: "345 Chambers St, New York, NY 10282",
    latitude: 40.7178,
    longitude: -74.0139,
    zone_radius: 300,
    historical_incidents: 28,
    double_parking_factor: 1.10,
    base_risk: 55.0
  },
  {
    id: "school_3",
    name: "Brooklyn Technical High School (Fort Greene)",
    address: "29 Ft Greene Pl, Brooklyn, NY 11217",
    latitude: 40.6888,
    longitude: -73.9765,
    zone_radius: 300,
    historical_incidents: 39,
    double_parking_factor: 1.45,
    base_risk: 68.0
  },
  {
    id: "school_4",
    name: "Bronx High School of Science (Bedford Park)",
    address: "75 W 205th St, Bronx, NY 10468",
    latitude: 40.8776,
    longitude: -73.8903,
    zone_radius: 300,
    historical_incidents: 19,
    double_parking_factor: 1.20,
    base_risk: 48.0
  }
];

function App() {
  const [route, setRoute] = useState(window.location.pathname);
  const [theme, setTheme] = useState<'light' | 'dark'>((localStorage.getItem('theme') as 'light' | 'dark') || 'light');
  const [user, setUser] = useState<{ email: string; name: string; role: 'super_admin' | 'public'; token: string } | null>(() => {
    const saved = localStorage.getItem('user_session');
    return saved ? JSON.parse(saved) : null;
  });

  const navigateTo = (path: string) => {
    window.history.pushState({}, '', path);
    setRoute(path);
  };

  useEffect(() => {
    const handlePopState = () => {
      setRoute(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const handleLogout = () => {
    localStorage.removeItem('user_session');
    setUser(null);
    navigateTo('/');
  };

  if (route === '/login') {
    return <LoginPage navigateTo={navigateTo} setUser={setUser} theme={theme} toggleTheme={toggleTheme} />;
  } else if (route === '/dashboard') {
    if (!user) {
      setTimeout(() => navigateTo('/login'), 50);
      return <div style={{ padding: '40px', textAlign: 'center', fontWeight: '800' }}>Redirecting to Login...</div>;
    }
    return <DashboardPage user={user} handleLogout={handleLogout} theme={theme} toggleTheme={toggleTheme} />;
  } else {
    return <LandingPage navigateTo={navigateTo} theme={theme} toggleTheme={toggleTheme} user={user} />;
  }
}

/* ==========================================================================
   LANDING PAGE COMPONENT (Landing Demo remains identical)
   ========================================================================== */
function LandingPage({ navigateTo, theme, toggleTheme, user }: { navigateTo: (path: string) => void; theme: string; toggleTheme: () => void; user: any }) {
  const [sliderIndex, setSliderIndex] = useState(3);

  const timelineDemo = [
    { time: "07:00 AM", score: 12, level: "low", title: "Clear Roads", factors: ["Minimal traffic flow", "Excellent morning sunlight"] },
    { time: "07:15 AM", score: 21, level: "low", title: "Slight Congestion", factors: ["Buses arriving at school terminal", "Normal speed limits active"] },
    { time: "07:30 AM", score: 38, level: "low", title: "Active Drop-off Starting", factors: ["Volunteer crossing guard arriving", "Moderate parent vehicles queue"] },
    { time: "07:45 AM", score: 54, level: "medium", title: "Traffic Congestion Building", factors: ["Drop-off queues extending to corner", "Pedestrian crosswalk density rising"] },
    { time: "08:00 AM", score: 88, level: "high", title: "Peak Congestion Spike 🚨", factors: ["Bell-time drop-off rush", "Frequent double-parking in live lanes", "Crossing guard gridlock"] },
    { time: "08:15 AM", score: 72, level: "high", title: "High Bell-Time Overflow 🚨", factors: ["Late-arrival pedestrian rush", "Congestion near crosswalk blocks sightlines"] },
    { time: "08:30 AM", score: 42, level: "medium", title: "Congestion Clearing", factors: ["Drop-off zone clearing", "Normal traffic flow resuming"] },
    { time: "08:45 AM", score: 25, level: "low", title: "Clear Roadway Flow", factors: ["Drop-off period complete", "Buses departed"] },
    { time: "09:00 AM", score: 10, level: "low", title: "Normal Neighborhood Flow", factors: ["Baseline street patterns"] }
  ];

  const currentDemo = timelineDemo[sliderIndex];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <header>
        <div className="container nav-container">
          <a href="#" onClick={(e) => { e.preventDefault(); navigateTo('/'); }} className="logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="M12 8v8"/>
              <path d="M8 12h8"/>
            </svg>
            <span className="logo-text">ZONE GUARDIAN</span>
          </a>
          <nav className="nav-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigateTo('/'); }} className="nav-link active">Home</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigateTo('/dashboard'); }} className="nav-link">Dashboard</a>
            {user ? (
              <button onClick={() => navigateTo('/dashboard')} className="btn-tactile btn-blue" style={{ padding: '8px 16px', fontSize: '14px' }}>Dashboard</button>
            ) : (
              <button onClick={() => navigateTo('/login')} className="btn-tactile btn-blue" style={{ padding: '8px 16px', fontSize: '14px' }}>Sign In</button>
            )}
            <button onClick={toggleTheme} className="theme-toggle" title="Toggle Dark/Light Mode">
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </nav>
        </div>
      </header>

      <section className="hero">
        <div className="container hero-content">
          <div className="hero-text">
            <h1>Safe Starts, <br/><span>Happy Hearts.</span></h1>
            <p>An AI-powered Decision Intelligence Platform predicting high-congestion risk windows. Plan safer routes, optimal drop-off timings, and coordinate safety guards.</p>
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              <button onClick={() => navigateTo('/dashboard')} className="btn-tactile btn-green" style={{ fontSize: '18px', padding: '16px 32px' }}>Go to Dashboard</button>
              <a href="#demo" className="btn-tactile" style={{ fontSize: '18px', padding: '16px 32px', textDecoration: 'none', display: 'flex', alignItems: 'center' }}>See How It Works</a>
            </div>
          </div>
          <div className="hero-mascot-container">
            <svg className="mascot-svg" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="100" cy="110" r="70" fill="#58cc02"/>
              <circle cx="100" cy="110" r="55" fill="#a5f3fc" opacity="0.15"/>
              <path d="M85 120 Q100 135 115 120" stroke="#46a302" strokeWidth="4" strokeLinecap="round"/>
              <path d="M90 135 Q100 145 110 135" stroke="#46a302" strokeWidth="4" strokeLinecap="round"/>
              <path d="M30 110 Q10 130 30 150" fill="#46a302" stroke="#46a302" strokeWidth="6" strokeLinecap="round"/>
              <path d="M170 110 Q190 130 170 150" fill="#46a302" stroke="#46a302" strokeWidth="6" strokeLinecap="round"/>
              <circle cx="70" cy="80" r="22" fill="#ffffff" stroke="#46a302" strokeWidth="4"/>
              <circle cx="130" cy="80" r="22" fill="#ffffff" stroke="#46a302" strokeWidth="4"/>
              <circle cx="74" cy="80" r="10" fill="#3c3c3c"/>
              <circle cx="126" cy="80" r="10" fill="#3c3c3c"/>
              <circle cx="77" cy="77" r="4" fill="#ffffff"/>
              <circle cx="129" cy="77" r="4" fill="#ffffff"/>
              <path d="M100 90 L110 102 L90 102 Z" fill="#ff8600"/>
              <path d="M50 50 L75 56 L65 72 Z" fill="#46a302"/>
              <path d="M150 50 L125 56 L135 72 Z" fill="#46a302"/>
              <circle cx="80" cy="178" r="8" fill="#ff8600"/>
              <circle cx="120" cy="178" r="8" fill="#ff8600"/>
              <g transform="translate(85, 120) scale(0.6)">
                <path d="M25 0 L50 10 L50 35 C50 50 25 60 25 60 C25 60 0 50 0 35 L0 10 Z" fill="#ffc800" stroke="#e6b400" strokeWidth="4"/>
                <path d="M25 15 L25 45" stroke="#ffffff" strokeWidth="6" strokeLinecap="round"/>
                <path d="M15 30 L35 30" stroke="#ffffff" stroke-width="6" strokeLinecap="round"/>
              </g>
            </svg>
          </div>
        </div>
      </section>

      <section id="demo" className="features-section" style={{ backgroundColor: 'var(--bg-color)' }}>
        <div className="container">
          <div className="demo-title" style={{ textAlign: 'center', marginBottom: '32px' }}>
            <h2 style={{ fontSize: '36px', marginBottom: '12px' }}>Pre-aggregate Spatial Hazards</h2>
            <p style={{ fontSize: '18px' }}>Slide the timeline to see how local weather shifts and bell-time drops increase safety risks in real-time.</p>
          </div>

          <div className="risk-demo-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', flexWrap: 'wrap', gap: '24px', marginBottom: '32px' }}>
              <div style={{ textAlign: 'center' }}>
                <div className={`score-circle ${currentDemo.level}`}>{currentDemo.score}</div>
                <div style={{ marginTop: '12px', fontWeight: '800', textTransform: 'uppercase', fontSize: '13px', letterSpacing: '0.8px', color: 'var(--text-secondary)' }}>Safety Risk Index</div>
              </div>
              <div style={{ maxWidth: '400px', flexGrow: 1 }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '10px' }}>
                  <span className={`badge-risk ${currentDemo.level}`} style={{ fontSize: '14px' }}>
                    {currentDemo.level.toUpperCase()} RISK
                  </span>
                  <span style={{ fontWeight: '800', fontSize: '14px', color: 'var(--text-secondary)' }}>{currentDemo.time}</span>
                </div>
                <h3>{currentDemo.title}</h3>
                <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', fontWeight: 500, margin: '8px 0 0 0' }}>
                  {currentDemo.factors.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              </div>
            </div>

            <div className="demo-slider-wrapper">
              <input 
                type="range" 
                min="0" 
                max="8" 
                value={sliderIndex} 
                className="timeline-slider" 
                onChange={(e) => setSliderIndex(parseInt(e.target.value))}
              />
              <div className="timeline-labels">
                <span>07:00 AM</span>
                <span>07:30 AM</span>
                <span>08:00 AM</span>
                <span>08:30 AM</span>
                <span>09:00 AM</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer style={{ marginTop: 'auto', borderTop: '2px solid var(--border-color)', padding: '16px 0', textAlign: 'center' }}>
        <p>&copy; 2026 School-Zone Guardian. Built for Google Cloud Hackathon. All rights reserved.</p>
      </footer>
    </div>
  );
}

/* ==========================================================================
   LOGIN PAGE COMPONENT
   ========================================================================== */
function LoginPage({ navigateTo, setUser, theme, toggleTheme }: { navigateTo: (path: string) => void; setUser: (u: any) => void; theme: string; toggleTheme: () => void }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [mockGmailInput, setMockGmailInput] = useState('');
  const [showMockGooglePanel, setShowMockGooglePanel] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Login failed. Please verify credentials.');
      }

      const sessionUser = {
        email: data.user.email,
        name: data.user.name,
        role: data.user.role,
        token: data.token
      };
      localStorage.setItem('user_session', JSON.stringify(sessionUser));
      setUser(sessionUser);
      navigateTo('/dashboard');
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const handleMockGoogleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!mockGmailInput.trim().toLowerCase().endsWith('@gmail.com')) {
      setErrorMsg('Google login is restricted to @gmail.com addresses only.');
      return;
    }

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: mockGmailInput })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Mock auth failed.');
      }

      const sessionUser = {
        email: data.user.email,
        name: data.user.name,
        role: data.user.role,
        token: data.token
      };
      localStorage.setItem('user_session', JSON.stringify(sessionUser));
      setUser(sessionUser);
      navigateTo('/dashboard');
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <header>
        <div className="container nav-container">
          <a href="#" onClick={(e) => { e.preventDefault(); navigateTo('/'); }} className="logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="M12 8v8"/>
              <path d="M8 12h8"/>
            </svg>
            <span>ZONE GUARDIAN</span>
          </a>
          <nav className="nav-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigateTo('/'); }} className="nav-link">Home</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigateTo('/dashboard'); }} className="nav-link">Dashboard</a>
            <button onClick={toggleTheme} className="theme-toggle" title="Toggle Dark/Light Mode">
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </nav>
        </div>
      </header>

      <div className="auth-container" style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 16px' }}>
        <div className="lingo-card auth-card" style={{ width: '100%', maxWidth: '420px' }}>
          <h2 className="auth-title">{showMockGooglePanel ? "Mock Google Sign In" : (isRegister ? "Create Account" : "Welcome Back!")}</h2>
          
          {errorMsg && (
            <div style={{ backgroundColor: 'var(--lingo-red)', color: 'white', padding: '12px', borderRadius: 'var(--radius-sm)', marginBottom: '16px', fontWeight: '700', fontSize: '13px' }}>
              ⚠️ {errorMsg}
            </div>
          )}

          {showMockGooglePanel ? (
            <form onSubmit={handleMockGoogleAuthSubmit}>
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label className="form-label">Gmail Address</label>
                <input 
                  className="form-input" 
                  type="email" 
                  required 
                  value={mockGmailInput}
                  onChange={(e) => setMockGmailInput(e.target.value)}
                  placeholder="yourname@gmail.com"
                />
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', display: 'block' }}>
                  Public access is restricted to @gmail.com addresses.
                </span>
              </div>
              
              <div style={{ display: 'flex', gap: '12px' }}>
                <button type="button" onClick={() => setShowMockGooglePanel(false)} className="btn-tactile" style={{ flexGrow: 1 }}>Back</button>
                <button type="submit" className="btn-tactile btn-green" style={{ flexGrow: 2 }}>Authenticate</button>
              </div>
            </form>
          ) : (
            <>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label className="form-label" htmlFor="email">Email Address</label>
                  <input 
                    className="form-input" 
                    type="email" 
                    id="email" 
                    required 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@domain.com"
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label" htmlFor="password">Password</label>
                  <input 
                    className="form-input" 
                    type="password" 
                    id="password" 
                    required 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                  />
                </div>
                
                <button type="submit" className="btn-tactile btn-green form-submit-btn" style={{ width: '100%', marginTop: '16px' }}>
                  {isRegister ? "Sign Up" : "Sign In"}
                </button>
              </form>
              
              <div style={{ display: 'flex', alignItems: 'center', margin: '24px 0' }}>
                <hr style={{ flexGrow: 1, border: 'none', borderTop: '2px solid var(--border-color)' }}/>
                <span style={{ padding: '0 16px', fontWeight: 800, color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'uppercase' }}>or</span>
                <hr style={{ flexGrow: 1, border: 'none', borderTop: '2px solid var(--border-color)' }}/>
              </div>
              
              <button onClick={() => setShowMockGooglePanel(true)} className="btn-tactile social-login-btn" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <svg width="20" height="20" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Sign In with Google (Gmail only)
              </button>
              
              <p className="auth-switch" style={{ textAlign: 'center', marginTop: '20px', fontSize: '14px' }}>
                {isRegister ? "Already have an account? " : "Don't have an account? "}
                <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(!isRegister); }} style={{ color: 'var(--lingo-blue)', fontWeight: 800 }}>
                  {isRegister ? "Sign In" : "Sign Up"}
                </a>
              </p>
              
              <div style={{ marginTop: '16px', padding: '12px', border: '1px dashed var(--border-color)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-secondary)', textAlign: 'center' }}>
                <strong>Admin credentials:</strong> yudhae@gmail.com / Password!123
              </div>
            </>
          )}
        </div>
      </div>

      <footer style={{ borderTop: '2px solid var(--border-color)', padding: '16px 0', textAlign: 'center' }}>
        <p>&copy; 2026 School-Zone Guardian. All rights reserved.</p>
      </footer>
    </div>
  );
}

/* ==========================================================================
   DASHBOARD PAGE COMPONENT (Role-based access tabs)
   ========================================================================== */
function DashboardPage({ user, handleLogout, theme, toggleTheme }: { user: any; handleLogout: () => void; theme: string; toggleTheme: () => void }) {
  const [schools, setSchools] = useState<School[]>(FALLBACK_SCHOOLS);
  const [headerAlert, setHeaderAlert] = useState<string | null>(null);
  const [selectedSchool, setSelectedSchool] = useState<School>(FALLBACK_SCHOOLS[1]); // default Stuyvesant
  const [rainProb, setRainProb] = useState(0.0); // 0 = clear, 0.8 = rain
  const [weatherInputChecked, setWeatherInputChecked] = useState(false);

  // Active Tab
  const [activeTab, setActiveTab] = useState<'dashboard' | 'chat' | 'admin' | 'hazard' | 'briefing'>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Simulation Parameters
  const [guardCount, setGuardCount] = useState(0);
  const [laneClosure, setLaneClosure] = useState(false);
  const [parentCompliance, setParentCompliance] = useState(100); // 70 to 130 %

  // Dynamic values returned from API
  const [riskSlots, setRiskSlots] = useState<RiskSlot[]>([]);
  const [activeSlotIndex, setActiveSlotIndex] = useState(4); // default "08:00-08:15"
  const [liveWeather, setLiveWeather] = useState<{ is_live_api: boolean; precipitation_probability_percent: number } | null>(null);

  // Active Hazards list
  const [activeHazards, setActiveHazards] = useState<Hazard[]>([]);

  // Volunteer shifts list
  const [volunteerRoster, setVolunteerRoster] = useState<VolunteerShift[]>([]);

  // Predictive ARIMA & Automation states
  const [arimaForecasts, setArimaForecasts] = useState<any[]>([]);
  const [arimaLoading, setArimaLoading] = useState(false);
  const [gcpMlActive, setGcpMlActive] = useState(false);
  const [automationLogs, setAutomationLogs] = useState<string[]>([]);
  const [automationLoading, setAutomationLoading] = useState(false);
  const [activeAgentLogs, setActiveAgentLogs] = useState<string[]>([]);


  // Chatbot states
  const [chatHistory, setChatHistory] = useState<ChatBubble[]>([
    { sender: 'bot', text: "Hello! I am Guardy, your School-Zone Guardian AI assistant. 🦉\n\nI have analyzed the spatial datasets for this school.\n\nHere is a quick snapshot of the current safety profile:\n* Nearby historical collisions: 28 incidents.\n* Primary Hazard Factor: High density drop-off double-parking.\n\nYou can ask me questions like:\n* _'When is the safest time to drop off my kids?'_\n* _'What are the main risk factors here?'_\n* _'How does rain affect the risk index?'_" }
  ]);
  const [chatMessage, setChatMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Photo Upload states
  const [, setSelectedHazardFile] = useState<File | null>(null);
  const [hazardPreviewUrl, setHazardPreviewUrl] = useState<string | null>(null);
  const [hazardAnalysisState, setHazardAnalysisState] = useState<'idle' | 'loading' | 'result'>('idle');
  const [analyzedHazardData, setAnalyzedHazardData] = useState<Hazard | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Admin Newsletter generator states
  const [isGeneratingNewsletter, setIsGeneratingNewsletter] = useState(false);
  const [newsletterHtml, setNewsletterHtml] = useState('');

  // Looker Studio Panel view switcher ('local' | 'live')
  const [lookerViewMode, setLookerViewMode] = useState<'local' | 'live'>('local');

  // Fetch school list on mount
  useEffect(() => {
    const fetchSchools = async () => {
      try {
        const response = await fetch('/api/schools');
        if (response.ok) {
          const data = await response.json();
          if (data && data.length > 0) {
            setSchools(data);
          }
        }
      } catch (e) {
        console.error("Failed to fetch schools, using fallback list:", e);
      }
    };
    fetchSchools();
  }, []);

  // Sync Weather checkbox with rain probability (0.0 or 0.8)
  useEffect(() => {
    setRainProb(weatherInputChecked ? 0.8 : 0.0);
  }, [weatherInputChecked]);

  // Global risk slots and simulation values loader
  const loadSchoolRiskData = async () => {
    try {
      const complianceFloat = parentCompliance / 100.0;
      const url = `/api/risk/${selectedSchool.id}?rain_prob=${rainProb}&guard_count=${guardCount}&lane_closure=${laneClosure}&parent_compliance=${complianceFloat}`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setRiskSlots(data.slots || []);
        setLiveWeather(data.live_weather || null);
      }
    } catch (e) {
      console.error("Failed to load school risk indexes: ", e);
    }
  };

  // Load Active Hazards for Selected School
  const loadActiveHazards = async () => {
    try {
      const response = await fetch(`/api/hazards/${selectedSchool.id}`);
      if (response.ok) {
        const data = await response.json();
        setActiveHazards(data || []);
      }
    } catch (e) {
      console.error("Failed to load active hazards: ", e);
    }
  };

  // Load Volunteer Shifts
  const loadVolunteerShifts = async () => {
    try {
      const response = await fetch(`/api/volunteers/${selectedSchool.id}`);
      if (response.ok) {
        const data = await response.json();
        setVolunteerRoster(data || []);
      }
    } catch (e) {
      console.error("Failed to load volunteer roster: ", e);
    }
  };

  // Load latest safety briefing
  const loadLatestBriefing = async () => {
    try {
      const response = await fetch(`/api/newsletter/latest?school_id=${selectedSchool.id}`);
      if (response.ok) {
        const data = await response.json();
        setNewsletterHtml(data.newsletter_html || '');
      }
    } catch (e) {
      console.error("Failed to load safety briefing: ", e);
    }
  };

  // Fetch BigQuery ML ARIMA forecasting weekly trend
  const loadSchoolPredictiveForecast = async () => {
    setArimaLoading(true);
    try {
      const response = await fetch(`/api/predictive/forecast?school_id=${selectedSchool.id}`);
      if (response.ok) {
        const data = await response.json();
        setArimaForecasts(data.forecasts || []);
        setGcpMlActive(data.gcp_ml_active || false);
      }
    } catch (e) {
      console.error("Failed to load arima forecasts: ", e);
    } finally {
      setArimaLoading(false);
    }
  };

  // Reload everything when school, rain probability, simulator variables change
  useEffect(() => {
    loadSchoolRiskData();
    loadActiveHazards();
    loadVolunteerShifts();
    loadLatestBriefing();
    loadSchoolPredictiveForecast();
  }, [selectedSchool, rainProb, guardCount, laneClosure, parentCompliance]);


  // Handle volunteer creation using browser native prompt popups
  const handleAddVolunteerPrompts = async () => {
    const name = prompt("Enter parent volunteer name:");
    if (!name) return;

    const zone = prompt("Enter assignment zone (e.g. Crossing Zone A, Entrance Gate):", "Crossing Zone A");
    if (!zone) return;

    const timeWindow = prompt("Enter safety shift window (e.g. 07:45-08:00, 08:00-08:15):", "07:45-08:15");
    if (!timeWindow) return;

    const today = new Date().toISOString().split('T')[0];

    try {
      const response = await fetch('/api/volunteers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({
          school_id: selectedSchool.id,
          volunteer_name: name,
          assigned_zone: zone,
          time_window: timeWindow,
          shift_date: today
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to add shift.");
      }

      loadVolunteerShifts();
      loadSchoolRiskData();
      alert(`Volunteer shift for ${name} successfully created!`);
    } catch (err: any) {
      alert(`Error adding shift: ${err.message}`);
    }
  };

  // Generate PTA Newsletter
  const handleGenerateNewsletter = async () => {
    setIsGeneratingNewsletter(true);
    setNewsletterHtml('');
    setHeaderAlert("⚡ COMPILING AI PTA BRIEFING...");
    try {
      const response = await fetch(`/api/newsletter/generate?school_id=${selectedSchool.id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}` }
      });
      const data = await response.json();
      if (response.ok) {
        setNewsletterHtml(data.newsletter_html || '');
        setHeaderAlert("✨ AI Safety Briefing Generated successfully!");
        setActiveTab('briefing');
        setTimeout(() => setHeaderAlert(null), 5000);
      } else {
        alert(data.detail || 'Newsletter generation failed.');
        setHeaderAlert("❌ GENERATION FAILED");
        setTimeout(() => setHeaderAlert(null), 5000);
      }
    } catch (e) {
      console.error("Newsletter error: ", e);
      alert('Error connecting to backend server.');
      setHeaderAlert("❌ SERVER ERROR");
      setTimeout(() => setHeaderAlert(null), 5000);
    } finally {
      setIsGeneratingNewsletter(false);
    }
  };

  // Chat message submit
  const handleChatSubmit = async (e?: React.FormEvent, customMsg?: string) => {
    if (e) e.preventDefault();
    const query = customMsg || chatMessage;
    if (!query.trim()) return;

    // Append user bubble
    setChatHistory(prev => [...prev, { sender: 'user', text: query }]);
    if (!customMsg) setChatMessage('');
    setChatLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          school_id: selectedSchool.id,
          history: []
        })
      });
      const data = await response.json();
      if (response.ok) {
        setChatHistory(prev => [...prev, { sender: 'bot', text: data.reply, grounded: data.gemini_active }]);
        if (data.agent_logs) {
          setActiveAgentLogs(data.agent_logs);
        }
      } else {
        setChatHistory(prev => [...prev, { sender: 'bot', text: `⚠️ Error: ${data.detail || 'Server connection failed.'}` }]);
      }
    } catch (err) {
      setChatHistory(prev => [...prev, { sender: 'bot', text: "Oops! Connection problem. Please verify backend running status." }]);
    } finally {
      setChatLoading(false);
    }
  };


  // Markdown parsing helper for AI chatbot bubbles
  const formatMarkdown = (text: string) => {
    return text
      .replace(/\n\n/g, '<br><br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>');
  };

  // Photo uploading drag-and-drop / selector handler
  const handleHazardFileSelect = (file: File | undefined) => {
    if (!file) return;

    setSelectedHazardFile(file);

    // Create preview URL
    const reader = new FileReader();
    reader.onload = function(e) {
      if (e.target?.result) {
        setHazardPreviewUrl(e.target.result as string);
      }
    };
    reader.readAsDataURL(file);

    setHazardAnalysisState('loading');
    setAnalyzedHazardData(null);

    uploadAndAnalyzeHazardPhoto(file);
  };

  const uploadAndAnalyzeHazardPhoto = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`/api/hazards/upload?school_id=${selectedSchool.id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${user.token}` },
        body: formData
      });
      const data = await response.json();
      if (response.ok) {
        setAnalyzedHazardData(data.hazard);
        setHazardAnalysisState('result');
      } else {
        alert("Vision analysis failed: " + (data.detail || 'Upload failed.'));
        resetHazardUploadZone();
      }
    } catch (err) {
      console.error(err);
      alert('Failed connecting to Gemini Vision API.');
      resetHazardUploadZone();
    }
  };

  const resetHazardUploadZone = () => {
    setSelectedHazardFile(null);
    setHazardPreviewUrl(null);
    setHazardAnalysisState('idle');
    setAnalyzedHazardData(null);
  };

  const submitHazardToDB = () => {
    if (!analyzedHazardData) return;
    alert("Traffic hazard successfully saved to safety database. Risk scores updated!");
    resetHazardUploadZone();
    loadActiveHazards();
    loadSchoolRiskData(); // Dynamic dial updating
  };

  const activeSlot: RiskSlot = riskSlots[activeSlotIndex] || {
    time_window: "08:00-08:15",
    score: selectedSchool.base_risk,
    level: "MEDIUM",
    weather_multiplier: 1.0,
    factors: ["Default base line congestion values"]
  };

  // Calculate local view metrics
  const avgScore = riskSlots.length > 0 
    ? Math.round(riskSlots.reduce((acc, s) => acc + s.score, 0) / riskSlots.length) 
    : 54;

  const getAvgScoreColor = () => {
    if (avgScore < 40) return '#109618'; // green
    if (avgScore < 70) return '#f2994a'; // orange
    return '#ea4335'; // red
  };

  // Calculate local factor percentages dynamically
  const factor1 = Math.min(80, Math.round(45 * selectedSchool.double_parking_factor));
  const factor2 = Math.min(50, Math.round(30 / selectedSchool.double_parking_factor));
  const factor3 = Math.max(10, 100 - factor1 - factor2);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <header className={headerAlert ? 'header-active-briefing' : ''}>
        <div className="container nav-container">
          <button className="hamburger-btn" onClick={() => setSidebarOpen(!sidebarOpen)} title="Toggle Menu">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          
          <a href="#" onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); setSidebarOpen(false); }} className="logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="M12 8v8"/>
              <path d="M8 12h8"/>
            </svg>
            <span className="logo-text">ZONE GUARDIAN</span>
          </a>
          
          {headerAlert && (
            <span className="header-alert-pill">
              {headerAlert}
            </span>
          )}
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginLeft: 'auto', marginRight: '16px' }}>
            <span className="gcp-id-label" style={{ fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', fontSize: '13px' }}>
              GCP ID: juaravibe01
            </span>
            <span style={{ fontSize: '13px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: 'var(--bg-secondary)', padding: '6px 12px', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
              <User size={14} />
              <span className="user-email-label">{user.email}</span>
              <span className={`badge-risk ${user.role === 'super_admin' ? 'high' : 'low'}`} style={{ fontSize: '10px', padding: '2px 6px', margin: 0 }}>
                {user.role === 'super_admin' ? 'ADMIN' : 'PUBLIC'}
              </span>
            </span>
          </div>

          <button onClick={toggleTheme} className="theme-toggle" title="Toggle Dark/Light Mode" style={{ marginRight: '16px' }}>
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>

      <div className="dashboard-wrapper" style={{ flexGrow: 1 }}>
        {sidebarOpen && (
          <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
        )}
        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <svg style={{ width: '32px', height: '32px', color: 'var(--lingo-green)' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span style={{ fontWeight: '800', fontSize: '18px' }}>PLATFORM MENU</span>
          </div>

          <div className="sidebar-menu">
            <button 
              onClick={() => { setActiveTab('dashboard'); setSidebarOpen(false); }} 
              className={`btn-tactile sidebar-menu-btn tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '10px' }}>
                <rect x="3" y="3" width="7" height="9"/>
                <rect x="14" y="3" width="7" height="5"/>
                <rect x="14" y="12" width="7" height="9"/>
                <rect x="3" y="16" width="7" height="5"/>
              </svg>
              Safety Dashboard
            </button>

            <button 
              onClick={() => { setActiveTab('chat'); setSidebarOpen(false); }} 
              className={`btn-tactile sidebar-menu-btn tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '10px' }}>
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              Guardian AI Chat
            </button>

            {user.role === 'super_admin' && (
              <button 
                onClick={() => { setActiveTab('admin'); setSidebarOpen(false); }} 
                className={`btn-tactile sidebar-menu-btn tab-btn ${activeTab === 'admin' ? 'active' : ''}`}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '10px' }}>
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                Admin Weekly Digest
              </button>
            )}

            <button 
              onClick={() => { setActiveTab('briefing'); setSidebarOpen(false); }} 
              className={`btn-tactile sidebar-menu-btn tab-btn ${activeTab === 'briefing' ? 'active' : ''}`}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '10px' }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              AI Safety Briefing
            </button>

            <button 
              onClick={() => { setActiveTab('hazard'); setSidebarOpen(false); }} 
              className={`btn-tactile sidebar-menu-btn tab-btn ${activeTab === 'hazard' ? 'active' : ''}`}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '10px' }}>
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              Report Safety Hazard
            </button>

            <button 
              onClick={handleLogout} 
              className="btn-tactile sidebar-menu-btn logout-btn"
              style={{ marginTop: '20px', borderColor: 'var(--lingo-red)', color: 'var(--lingo-red)' }}
            >
              <LogOut size={18} style={{ marginRight: '10px' }} />
              Log Out
            </button>
          </div>

          <div className="sidebar-mascot" style={{ marginTop: 'auto', padding: '16px', border: '2px solid var(--border-color)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--bg-secondary)' }}>
            <p style={{ fontWeight: '700', fontSize: '13px', margin: '0 0 6px 0' }}>SAFETY OWL MASCOT</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <svg width="32" height="32" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="#58cc02"/>
                <circle cx="35" cy="40" r="12" fill="white"/>
                <circle cx="65" cy="40" r="12" fill="white"/>
                <circle cx="36" cy="40" r="5" fill="#3c3c3c"/>
                <circle cx="64" cy="40" r="5" fill="#3c3c3c"/>
                <path d="M50 48 L55 55 L45 55 Z" fill="#ff8600"/>
              </svg>
              <span style={{ fontSize: '14px', fontWeight: '700' }}>
                {activeSlot.level === 'HIGH' ? '"Be careful!"' : '"Looking clear!"'}
              </span>
            </div>
          </div>
        </aside>

        <main className="main-content" style={{ flexGrow: 1 }}>
          
          <div className="school-selector-card">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontWeight: 800, fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Select Active School</label>
              <select 
                className="select-tactile" 
                value={selectedSchool.id}
                onChange={(e) => {
                  const sc = schools.find(s => s.id === e.target.value);
                  if (sc) setSelectedSchool(sc);
                }}
              >
                {schools.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginLeft: 'auto' }}>
              <label style={{ fontWeight: 800, fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Current Weather</label>
              <label className="toggle-container">
                <input 
                  type="checkbox" 
                  style={{ display: 'none' }}
                  checked={weatherInputChecked}
                  onChange={(e) => setWeatherInputChecked(e.target.checked)}
                />
                <div className="switch-tactile"></div>
                <span style={{ fontSize: '15px', fontWeight: '700' }}>
                  {weatherInputChecked ? '🌧️ Rainy Weather' : '☀️ Clear Weather'}
                  {liveWeather && liveWeather.precipitation_probability_percent > 0 && ` (${liveWeather.precipitation_probability_percent}% precip)`}
                </span>
              </label>
            </div>
          </div>

          {/* ==================== PANEL: SAFETY DASHBOARD ==================== */}
          {activeTab === 'dashboard' && (
            <div className="tab-content active" style={{ display: 'block' }}>
              <h2>Spatial Safety Risk Index</h2>
              <p>Pre-calculated database aggregation joining localized crash points within 300m buffers.</p>

              <div className="panel-grid">
                
                {/* 1. Map Panel (Left) */}
                <div className="lingo-card" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: '400px' }}>
                  <div style={{ padding: '16px 24px', borderBottom: '2px solid var(--border-color)', fontWeight: 800, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>ZONE BUFFER (300 METERS)</span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                      {selectedSchool.latitude}° N, {Math.abs(selectedSchool.longitude)}° W
                    </span>
                  </div>
                  <MapComponent 
                    latitude={selectedSchool.latitude || 40.7178} 
                    longitude={selectedSchool.longitude || -74.0139} 
                    schoolName={selectedSchool.name}
                    historicalIncidents={selectedSchool.historical_incidents} 
                    level={activeSlot.level} 
                    theme={theme}
                    activeHazards={activeHazards}
                  />
                </div>

                {/* 2. Safety Parameters Dial (Center) */}
                <div className="lingo-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '400px' }}>
                  <div style={{ textAlign: 'center' }}>
                    <h3 style={{ fontSize: '18px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '16px' }}>Current Safety Risk</h3>
                    <div className={`score-circle ${activeSlot.level.toLowerCase()}`}>{Math.round(activeSlot.score)}</div>
                    <span className={`badge-risk ${activeSlot.level.toLowerCase()}`} style={{ marginTop: '16px', fontSize: '16px', display: 'inline-block' }}>
                      {activeSlot.level} RISK
                    </span>
                  </div>

                  <div style={{ borderTop: '2px solid var(--border-color)', paddingTop: '16px', marginTop: '16px', textAlign: 'left' }}>
                    <h4 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '10px' }}>Primary Risk Drivers</h4>
                    <ul style={{ paddingLeft: '20px', fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {activeSlot.factors.map((f, i) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                </div>

                {/* 3. Scenario Simulator Card (Right) */}
                <div className="lingo-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '400px', textAlign: 'left' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '16px', borderBottom: '2px solid var(--border-color)', paddingBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      🎛️ Scenario Simulator
                    </h3>
                    <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: '1.4' }}>
                      Model operational adjustments and compliance to observe risk scores adapt instantly.
                    </p>
                    
                    {/* PTA Guards */}
                    <div style={{ marginBottom: '18px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700, marginBottom: '6px' }}>
                        <span>PTA Crossing Guards:</span>
                        <span style={{ color: 'var(--lingo-blue)', fontWeight: 800 }}>{guardCount} guard{guardCount === 1 ? '' : 's'}</span>
                      </div>
                      <input 
                        type="range" 
                        min="0" 
                        max="4" 
                        step="1" 
                        value={guardCount} 
                        onChange={(e) => setGuardCount(parseInt(e.target.value))}
                        className="select-tactile" 
                        style={{ width: '100%', cursor: 'pointer' }}
                      />
                    </div>
                    
                    {/* Lane closure toggle */}
                    <div style={{ marginBottom: '18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-secondary)', padding: '10px', borderRadius: '8px', border: '1.5px solid var(--border-color)' }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: '13px', fontWeight: 700 }}>Lane Closure Alert:</span>
                        <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>Model street closures</span>
                      </div>
                      <label className="toggle-container" style={{ margin: 0 }}>
                        <input 
                          type="checkbox" 
                          checked={laneClosure}
                          onChange={(e) => setLaneClosure(e.target.checked)}
                          style={{ display: 'none' }}
                        />
                        <div className="switch-tactile"></div>
                      </label>
                    </div>
                    
                    {/* Compliance slider */}
                    <div style={{ marginBottom: '10px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700, marginBottom: '6px' }}>
                        <span>Parent Drop-off Compliance:</span>
                        <span style={{ color: 'var(--lingo-green-shadow)', fontWeight: 800 }}>{parentCompliance}% compliance</span>
                      </div>
                      <input 
                        type="range" 
                        min="70" 
                        max="130" 
                        step="10" 
                        value={parentCompliance} 
                        onChange={(e) => setParentCompliance(parseInt(e.target.value))}
                        className="select-tactile" 
                        style={{ width: '100%', cursor: 'pointer' }}
                      />
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => {
                      setGuardCount(0);
                      setLaneClosure(false);
                      setParentCompliance(100);
                    }}
                    className="btn-tactile lingo-btn blue" 
                    style={{ width: '100%', padding: '10px', fontSize: '12px', marginTop: '10px' }}
                  >
                    🔄 Reset Parameters
                  </button>
                </div>

              </div>

              {/* Temporal Range Slider */}
              <div className="lingo-card" style={{ marginTop: '24px', textAlign: 'left' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '20px', margin: 0 }}>Micro-Window Temporal Timeline</h3>
                  <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--lingo-blue)' }}>
                    {activeSlot.time_window} AM
                  </span>
                </div>

                <div className="demo-slider-wrapper">
                  <input 
                    type="range" 
                    min="0" 
                    max={riskSlots.length > 0 ? riskSlots.length - 1 : 19} 
                    value={activeSlotIndex} 
                    onChange={(e) => setActiveSlotIndex(parseInt(e.target.value))}
                    className="timeline-slider"
                  />
                  <div className="timeline-labels" style={{ maxWidth: '100%' }}>
                    <span>07:00 AM</span>
                    <span>07:30 AM</span>
                    <span>08:00 AM</span>
                    <span>08:30 AM</span>
                    <span>09:00 AM</span>
                    <span>09:30 AM</span>
                  </div>
                </div>
              </div>

              {/* Explainable AI - Risk Factor Breakdown */}
              <div className="lingo-card" style={{ marginTop: '24px', textAlign: 'left' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '20px', margin: 0 }}>🔍 Explainable AI — Risk Breakdown</h3>
                  <span className={`badge-risk ${activeSlot.level.toLowerCase()}`} style={{ fontSize: '12px' }}>
                    {activeSlot.level} — {Math.round(activeSlot.score)}/100
                  </span>
                </div>
                
                {activeSlot.risk_breakdown && activeSlot.risk_breakdown.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {activeSlot.risk_breakdown.map((rb, i) => (
                      <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700 }}>
                          <span>{rb.factor}</span>
                          <span style={{ color: 'var(--lingo-blue)', fontWeight: 800 }}>
                            {rb.contribution.toFixed(1)} pts ({rb.weight}%)
                          </span>
                        </div>
                        <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--bg-secondary)', overflow: 'hidden' }}>
                          <div style={{ 
                            width: `${Math.min(100, rb.weight)}%`, 
                            height: '100%', 
                            borderRadius: '4px', 
                            background: rb.weight >= 30 ? '#ff4b4b' : rb.weight >= 20 ? '#ffc800' : '#58cc02',
                            transition: 'width 0.5s ease'
                          }} />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {activeSlot.factors.map((f, i) => {
                      const weight = Math.round(100 / Math.max(1, activeSlot.factors.length));
                      const contribution = (activeSlot.score * weight) / 100;
                      return (
                        <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700 }}>
                            <span>{f}</span>
                            <span style={{ color: 'var(--lingo-blue)', fontWeight: 800 }}>
                              {contribution.toFixed(1)} pts ({weight}%)
                            </span>
                          </div>
                          <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--bg-secondary)', overflow: 'hidden' }}>
                            <div style={{ 
                              width: `${Math.min(100, weight)}%`, 
                              height: '100%', 
                              borderRadius: '4px', 
                              background: weight >= 30 ? '#ff4b4b' : weight >= 20 ? '#ffc800' : '#58cc02',
                              transition: 'width 0.5s ease'
                            }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Responsible AI Notice */}
                <div style={{ marginTop: '20px', padding: '14px 18px', background: 'rgba(88, 204, 2, 0.08)', borderLeft: '4px solid var(--lingo-green, #58cc02)', borderRadius: '0 8px 8px 0' }}>
                  <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', fontWeight: 800, color: '#46a302' }}>🛡️ Responsible AI Transparency</h4>
                  <p style={{ margin: 0, fontSize: '12px', lineHeight: '1.5', color: 'var(--text-secondary)', fontWeight: 600 }}>
                    This score uses <strong>only physical safety variables</strong>: historical collision density, real-time weather, road closures, and user-reported hazards. 
                    No demographic, income, policing, or socioeconomic data is used. 
                    <br/>Data sources: NYPD Motor Vehicle Collisions (BigQuery Public), Open-Meteo Weather API, User-reported Hazards.
                  </p>
                </div>
              </div>

              {/* Feature 2: BigQuery ML ARIMA Time-Series Risk Forecasting */}
              <div className="lingo-card" style={{ marginTop: '24px', textAlign: 'left' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '20px', margin: 0 }}>📈 BigQuery ML — 7-Day Safety Risk Forecast</h3>
                  <span style={{ fontSize: '11px', padding: '4px 8px', borderRadius: '12px', background: gcpMlActive ? 'rgba(88, 204, 2, 0.12)' : 'var(--bg-secondary)', color: gcpMlActive ? '#58cc02' : 'var(--text-secondary)', fontWeight: 800 }}>
                    {gcpMlActive ? "📡 Live BigQuery ML (ARIMA+)" : "⚡ Local ARIMA Simulator"}
                  </span>
                </div>
                
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: '1.5' }}>
                  Autoregressive Integrated Moving Average (ARIMA) projection utilizing NYC NYPD Crash database tables to predict safety levels for the upcoming week.
                </p>

                {arimaLoading ? (
                  <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    <span>Loading ML projections...</span>
                  </div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '12px' }}>
                    {arimaForecasts.map((f, i) => {
                      const scoreColor = f.predicted_risk >= 70 ? '#ff4b4b' : f.predicted_risk >= 40 ? '#ffc800' : '#58cc02';
                      return (
                        <div key={i} style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '8px', border: '1.5px solid var(--border-color)', textAlign: 'center' }}>
                          <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{f.day.slice(0, 3)}</div>
                          <div style={{ fontSize: '10px', color: 'var(--text-secondary)', margin: '2px 0 6px 0' }}>{f.date.slice(5)}</div>
                          <div style={{ fontSize: '22px', fontWeight: 800, color: scoreColor }}>{Math.round(f.predicted_risk)}</div>
                          <div style={{ fontSize: '9px', color: 'var(--text-secondary)', marginTop: '4px', fontWeight: 700 }}>
                            Range: {Math.round(f.lower_bound)}-{Math.round(f.upper_bound)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

            </div>
          )}


          {/* ==================== PANEL: GUARDIAN AI CHAT ==================== */}
          {activeTab === 'chat' && (
            <div className="tab-content active" style={{ display: 'block' }}>
              <h2>Guardian AI Safety Chat</h2>
              <p>Get instant travel guidelines, dynamic safety alerts, and optimized arrival recommendations from our friendly assistant Guardy.</p>
              
              <div className="chat-container">
                <div className="chat-header">
                  <svg className="chat-mascot-icon" width="40" height="40" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="45" fill="#58cc02"/>
                    <circle cx="35" cy="40" r="12" fill="white"/>
                    <circle cx="65" cy="40" r="12" fill="white"/>
                    <circle cx="36" cy="40" r="5" fill="#3c3c3c"/>
                    <circle cx="64" cy="40" r="5" fill="#3c3c3c"/>
                    <path d="M50 48 L55 55 L45 55 Z" fill="#ff8600"/>
                  </svg>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '800' }}>Guardy</h4>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>School Zone Safety Assistant</span>
                  </div>
                </div>

                <div className="chat-messages" style={{ overflowY: 'auto' }}>
                  {chatHistory.map((bubble, i) => (
                    <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: bubble.sender === 'user' ? 'flex-end' : 'flex-start', margin: '4px 0' }}>
                      <div 
                        className={`chat-bubble ${bubble.sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'}`}
                        dangerouslySetInnerHTML={{ __html: formatMarkdown(bubble.text) }}
                      />
                      {bubble.sender === 'bot' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', fontWeight: 700, padding: '2px 8px', marginTop: '2px', color: 'var(--text-secondary)' }}>
                          {bubble.grounded ? (
                            <><span style={{ color: '#58cc02' }}>✅ RAG-Grounded</span> · Gemini 2.5 Flash · Data-verified</>
                          ) : (
                            <><span style={{ color: '#ffc800' }}>⚡ Rule Engine</span> · Local heuristics · Offline mode</>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="chat-bubble chat-bubble-bot" style={{ opacity: 0.6 }}>
                      <span style={{ fontStyle: 'italic' }}>Thinking...</span>
                    </div>
                  )}
                </div>

                {activeAgentLogs.length > 0 && (
                  <div style={{ background: 'var(--bg-secondary)', padding: '10px 24px', borderTop: '2px solid var(--border-color)', fontSize: '11px', textAlign: 'left' }}>
                    <details open>
                      <summary style={{ fontWeight: 800, cursor: 'pointer', color: 'var(--text-secondary)' }}>🤖 ADK Multi-Agent Execution Trace</summary>
                      <ul style={{ margin: '6px 0 0 0', paddingLeft: '20px', listStyleType: 'none', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {activeAgentLogs.map((log, index) => (
                          <li key={index} style={{ fontFamily: 'monospace', color: 'var(--text-secondary)', fontWeight: 600 }}>
                            {log}
                          </li>
                        ))}
                      </ul>
                    </details>
                  </div>
                )}


                <div style={{ display: 'flex', gap: '8px', padding: '12px 24px', flexWrap: 'wrap', borderTop: '2px solid var(--border-color)', background: 'var(--bg-secondary)' }}>
                  <button onClick={() => handleChatSubmit(undefined, "When is the safest time to drop off my children?")} className="btn-tactile" style={{ fontSize: '11px', padding: '6px 12px' }}>🕒 Safest Drop-off Windows</button>
                  <button onClick={() => handleChatSubmit(undefined, "What are the primary hazards around here?")} className="btn-tactile" style={{ fontSize: '11px', padding: '6px 12px' }}>🚨 Active Risk Drivers</button>
                  <button onClick={() => handleChatSubmit(undefined, "How does wet rain forecast modify the danger level?")} className="btn-tactile" style={{ fontSize: '11px', padding: '6px 12px' }}>🌧️ Weather Surcharge</button>
                  <button onClick={() => handleChatSubmit(undefined, "Compare risk levels across all schools and tell me which is safest")} className="btn-tactile" style={{ fontSize: '11px', padding: '6px 12px' }}>📊 Compare All Schools</button>
                  <button onClick={() => handleChatSubmit(undefined, "Show me the weekly risk trend analysis for this school")} className="btn-tactile" style={{ fontSize: '11px', padding: '6px 12px' }}>📈 Weekly Trend Analysis</button>
                  <button onClick={() => handleChatSubmit(undefined, "Analyze volunteer coverage gaps and recommend where more guards are needed")} className="btn-tactile" style={{ fontSize: '11px', padding: '6px 12px' }}>🔍 Volunteer Coverage Gaps</button>
                </div>

                <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '12px', padding: '16px 24px', borderTop: '2px solid var(--border-color)' }}>
                  <input 
                    className="form-input" 
                    value={chatMessage} 
                    onChange={(e) => setChatMessage(e.target.value)}
                    placeholder="Ask Guardy about traffic risk timings..."
                    style={{ flexGrow: 1 }}
                  />
                  <button type="submit" className="btn-tactile btn-blue" style={{ padding: '0 24px' }}>Send</button>
                </form>
              </div>
            </div>
          )}

          {/* ==================== PANEL: ADMIN WEEKLY DIGEST ==================== */}
          {activeTab === 'admin' && user.role === 'super_admin' && (
            <div className="tab-content active" style={{ display: 'block' }}>
              <h2>Administrator Weekly digest</h2>
              <p>Roster crossing guard positions and parent volunteers based on 15-minute high-risk spikes.</p>

              <div className="admin-panel-grid">
                
                {/* Left Column: Guard shift optimizer */}
                <div className="lingo-card" style={{ textAlign: 'left' }}>
                  <h3 style={{ marginBottom: '16px' }}>Crossing Guard Shift Optimizer</h3>
                  <div style={{ overflowX: 'auto', width: '100%' }}>
                    <table className="safety-table">
                    <thead>
                      <tr>
                        <th>Time Window</th>
                        <th>Risk Score</th>
                        <th>Roster Required</th>
                        <th>Suggested Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {riskSlots.slice(0, 7).map((slot, idx) => (
                        <tr key={idx}>
                          <td>{slot.time_window}</td>
                          <td>
                            <span className={`badge-risk ${slot.level.toLowerCase()}`}>{slot.score}</span>
                          </td>
                          <td>
                            {slot.level === 'HIGH' ? (
                              <strong style={{ color: 'var(--lingo-red)' }}>🚨 Full Patrol (3+ Guards)</strong>
                            ) : slot.level === 'MEDIUM' ? (
                              <span style={{ color: 'var(--lingo-orange-shadow)', fontWeight: '700' }}>⚠️ Standard (1-2 Volunteers)</span>
                            ) : (
                              <span style={{ color: 'var(--lingo-green-shadow)' }}>🟢 Minimal Monitor</span>
                            )}
                          </td>
                          <td>
                            {slot.level === 'HIGH' ? 'Deploy cones & slow signages' : slot.level === 'MEDIUM' ? 'Active crosswalk patrol' : 'Standard patrol presence'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  </div>
                  
                  <button onClick={() => window.print()} className="btn-tactile btn-blue" style={{ marginTop: '24px' }}>🖨️ Export PDF Safety Digest</button>
                </div>

                {/* Right Column: Volunteer Planner */}
                <div className="lingo-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', textAlign: 'left' }}>
                  <div>
                    <h3 style={{ marginBottom: '16px' }}>Volunteer Roster Deployment</h3>
                    <p style={{ marginBottom: '20px', fontSize: '14px' }}>Deploy volunteer parent captains at safety cones or drop-off intersections during red windows.</p>
                    
                    <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
                      {volunteerRoster.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '14px' }}>
                          No volunteers deployed for this week yet.
                        </div>
                      ) : (
                        volunteerRoster.map(s => {
                          let levelClass = 'low';
                          if (s.time_window.includes("07:45") || s.time_window.includes("08:00") || s.time_window.includes("15:00")) {
                            levelClass = 'high';
                          } else if (s.time_window.includes("07:30") || s.time_window.includes("14:30")) {
                            levelClass = 'medium';
                          }
                          return (
                            <div key={s.roster_id} className="roster-card">
                              <div>
                                <h4 style={{ fontSize: '15px', margin: 0 }}>{s.assigned_zone}</h4>
                                <p style={{ fontSize: '13px', margin: '4px 0 0 0' }}>Volunteer: <strong>{s.volunteer_name}</strong></p>
                              </div>
                              <span className={`badge-risk ${levelClass}`} style={{ flexShrink: 0 }}>{s.time_window}</span>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>

                  <button onClick={handleAddVolunteerPrompts} className="btn-tactile btn-green" style={{ width: '100%', marginTop: '20px' }}>
                    ➕ Add Volunteer Captain
                  </button>
                </div>

              </div>

              {/* Looker Studio BI Dashboard Panel */}
              <div className="lingo-card" style={{ marginTop: '24px', padding: 0, overflow: 'hidden', border: '2px solid var(--border-color)', textAlign: 'left' }}>
                <div style={{ backgroundColor: '#f8f9fa', borderBottom: '1px solid var(--border-color)', padding: '12px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', textAlign: 'left' }}>
                    <span style={{ fontSize: '20px' }}>📊</span>
                    <div>
                      <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#1a73e8' }}>Looker Studio - School Zone Spatial Analytics</h4>
                      <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-secondary)' }}>GCP Dataset: <code>juaravibe01:safety_dataset</code></p>
                    </div>
                  </div>
                  
                  {/* View Toggles */}
                  <div style={{ display: 'inline-flex', background: '#e8eaed', padding: '4px', borderRadius: '20px', fontSize: '12px', fontWeight: 700, border: '1px solid var(--border-color)' }}>
                    <span 
                      onClick={() => setLookerViewMode('local')} 
                      style={{ padding: '6px 14px', borderRadius: '16px', background: lookerViewMode === 'local' ? 'white' : 'transparent', color: lookerViewMode === 'local' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', transition: 'all 0.2s' }}
                    >
                      Local Charts
                    </span>
                    <span 
                      onClick={() => setLookerViewMode('live')} 
                      style={{ padding: '6px 14px', borderRadius: '16px', background: lookerViewMode === 'live' ? 'var(--lingo-blue)' : 'transparent', color: lookerViewMode === 'live' ? 'white' : 'var(--text-secondary)', cursor: 'pointer', transition: 'all 0.2s' }}
                    >
                      Live GCP Embed
                    </span>
                  </div>
                </div>

                {/* Local charts view */}
                {lookerViewMode === 'local' ? (
                  <div id="looker-local-view" style={{ padding: '24px', backgroundColor: '#f1f3f4', textAlign: 'left' }}>
                    {/* KPIs */}
                    <div className="looker-kpi-grid">
                      <div style={{ background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #dadce0', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Zone Incidents</div>
                        <div style={{ fontSize: '24px', fontWeight: 800, color: '#1a73e8' }}>{selectedSchool.historical_incidents}</div>
                        <div style={{ fontSize: '11px', color: 'var(--lingo-red)', fontWeight: 600, marginTop: '4px' }}>▲ +12% vs last year</div>
                      </div>
                      <div style={{ background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #dadce0', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Average Risk Index</div>
                        <div style={{ fontSize: '24px', fontWeight: 800, color: getAvgScoreColor() }}>{avgScore}%</div>
                        <div style={{ fontSize: '11px', color: 'var(--lingo-green-shadow)', fontWeight: 600, marginTop: '4px' }}>▼ -4% (Standard weather)</div>
                      </div>
                      <div style={{ background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #dadce0', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Ingested Boundaries</div>
                        <div style={{ fontSize: '24px', fontWeight: 800, color: '#109618' }}>4 zones</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600, marginTop: '4px' }}>Active spatial coordinates</div>
                      </div>
                      <div style={{ background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #dadce0', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Daily Spatial Joins</div>
                        <div style={{ fontSize: '24px', fontWeight: 800, color: '#990099' }}>124 runs</div>
                        <div style={{ fontSize: '11px', color: 'var(--lingo-green-shadow)', fontWeight: 600, marginTop: '4px' }}>✔ Scheduled query OK</div>
                      </div>
                    </div>

                    <div className="looker-charts-grid">
                      {/* Bar chart */}
                      <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #dadce0', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                        <h4 style={{ fontSize: '14px', color: 'var(--text-primary)', margin: '0 0 16px 0', fontWeight: 700 }}>Spatial Collision Distribution by Hour</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px', height: '180px', alignItems: 'end', background: '#fafafa', padding: '10px', borderRadius: '6px' }}>
                          {[
                            { time: "07 AM", val: riskSlots[0]?.score || 25 },
                            { time: "08 AM", val: riskSlots[4]?.score || 45 },
                            { time: "09 AM", val: riskSlots[6]?.score || 85 },
                            { time: "02 PM", val: riskSlots[10]?.score || 35 },
                            { time: "03 PM", val: riskSlots[14]?.score || 75 },
                            { time: "04 PM", val: riskSlots[18]?.score || 15 }
                          ].map((item, i) => (
                            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                              <div style={{ width: '100%', background: i === 2 ? '#ea4335' : '#4285f4', borderRadius: '4px', height: `${item.val}%`, transition: 'height 0.5s ease-out' }} />
                              <span style={{ fontSize: '10px', marginTop: '6px', color: 'var(--text-secondary)', fontWeight: 600 }}>{item.time}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Factor bars */}
                      <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #dadce0', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <h4 style={{ fontSize: '14px', color: 'var(--text-primary)', margin: '0 0 12px 0', fontWeight: 700 }}>Contributing Traffic Factors</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', fontWeight: 600 }}>
                          <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', margin: '0 0 4px 0' }}>
                              <span>Driver Inattention</span>
                              <span>{factor1}%</span>
                            </div>
                            <div style={{ background: '#e8f0fe', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ background: '#1a73e8', height: '100%', width: `${factor1}%`, transition: 'width 0.5s ease-out' }}></div>
                            </div>
                          </div>
                          <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', margin: '0 0 4px 0' }}>
                              <span>Failure to Yield Right of Way</span>
                              <span>{factor2}%</span>
                            </div>
                            <div style={{ background: '#e8f0fe', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ background: '#129618', height: '100%', width: `${factor2}%`, transition: 'width 0.5s ease-out' }}></div>
                            </div>
                          </div>
                          <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', margin: '0 0 4px 0' }}>
                              <span>Unsafe Speed</span>
                              <span>{factor3}%</span>
                            </div>
                            <div style={{ background: '#e8f0fe', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ background: '#f2994a', height: '100%', width: `${factor3}%`, transition: 'width 0.5s ease-out' }}></div>
                            </div>
                          </div>
                        </div>
                      </div>

                    </div>
                  </div>
                ) : (
                  <div id="looker-live-view" style={{ padding: '24px', backgroundColor: '#f1f3f4', textAlign: 'left' }}>
                    <div style={{ backgroundColor: 'rgba(66,133,244,0.08)', borderLeft: '4px solid #4285f4', padding: '12px 16px', borderRadius: '8px', marginBottom: '16px', fontSize: '13px', fontWeight: 600, color: '#1a73e8', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                      <span>🔗 Live Looker Studio report loaded directly from GCP datasets.</span>
                      <a href="https://lookerstudio.google.com/reporting/1da83ff5-3b0d-4629-867c-a79475390cab/page/8W72F" target="_blank" style={{ color: '#1a73e8', textDecoration: 'underline', fontWeight: 700, fontSize: '12px' }}>Open in New Tab ↗</a>
                    </div>
                    <div id="looker-frame-wrapper" style={{ width: '100%', height: '500px', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '2px solid var(--border-color)', background: 'white' }}>
                      <iframe 
                        id="looker-iframe" 
                        src="https://datastudio.google.com/embed/reporting/1da83ff5-3b0d-4629-867c-a79475390cab/page/8W72F" 
                        style={{ width: '100%', height: '100%', border: 'none' }} 
                        allowFullScreen 
                        sandbox="allow-storage-access-by-user-activation allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Local visualizer safety trend bar charts */}
              <div style={{ borderTop: '2px solid var(--border-color)', paddingTop: '20px', textAlign: 'left', marginTop: '24px' }}>
                <h4 style={{ fontSize: '16px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>📈 Dynamic Hazard Distribution Trend (Local Visualizer)</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', height: '180px', alignItems: 'end', background: 'var(--bg-secondary)', padding: '20px', borderRadius: 'var(--radius-sm)', border: '2px solid var(--border-color)' }}>
                  {[
                    { label: "07:00 AM", score: riskSlots[0]?.score || 30, color: 'var(--lingo-green)' },
                    { label: "07:30 AM", score: riskSlots[2]?.score || 55, color: 'var(--lingo-yellow-shadow)' },
                    { label: "08:00 AM", score: riskSlots[4]?.score || 90, color: 'var(--lingo-red)' },
                    { label: "08:30 AM", score: riskSlots[6]?.score || 65, color: 'var(--lingo-yellow-shadow)' },
                    { label: "09:00 AM", score: riskSlots[8]?.score || 25, color: 'var(--lingo-green)' }
                  ].map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                      <div style={{ width: '100%', background: item.color, borderRadius: '6px', transition: 'height 0.5s ease-out', height: `${item.score}%` }} />
                      <span style={{ fontSize: '11px', marginTop: '8px', fontWeight: 700, color: 'var(--text-secondary)' }}>{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Feature 7: Cloud Scheduler & Pub/Sub Workflow Automation Console */}
              <div className="lingo-card" style={{ marginTop: '24px', textAlign: 'left' }}>
                <h3 style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  ⚙️ GCP Workflow Automation Console (Scheduler & Pub/Sub)
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: '1.5' }}>
                  Simulate a scheduled event from <strong>Cloud Scheduler</strong> publishing to the <code>weather-updated</code> and <code>safety-alert-needed</code> <strong>Pub/Sub Topics</strong>. Triggers automated safety score recalculation and alert notifications.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px', flexWrap: 'wrap' }}>
                  {/* Left Column: Parameter controls */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', background: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1.5px solid var(--border-color)' }}>
                    <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800 }}>Simulate Event Inputs</h4>
                    
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 700, marginBottom: '6px' }}>
                        <span>Precipitation probability:</span>
                        <span style={{ color: 'var(--lingo-blue)' }}>{Math.round(rainProb * 100)}%</span>
                      </div>
                      <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step="0.1" 
                        value={rainProb} 
                        onChange={(e) => setRainProb(parseFloat(e.target.value))}
                        style={{ width: '100%', cursor: 'pointer' }}
                      />
                    </div>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 700, cursor: 'pointer' }}>
                      <input 
                        type="checkbox" 
                        id="simulate-hazard-checkbox"
                        style={{ width: '16px', height: '16px' }}
                      />
                      <span>Simulate New Hazard (Blocking)</span>
                    </label>

                    <button 
                      onClick={async () => {
                        setAutomationLoading(true);
                        try {
                          const simulateHazard = (document.getElementById('simulate-hazard-checkbox') as HTMLInputElement)?.checked || false;
                          const res = await fetch('/api/automation/trigger', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              school_id: selectedSchool.id,
                              simulate_rain_change: rainProb,
                              simulate_new_hazard: simulateHazard
                            })
                          });
                          if (res.ok) {
                            const data = await res.json();
                            setAutomationLogs(data.event_logs || []);
                            loadActiveHazards(); // Reload active hazards to show the automated alert!
                          }
                        } catch (err) {
                          console.error("Automation error: ", err);
                        } finally {
                          setAutomationLoading(false);
                        }
                      }}
                      className="btn-tactile btn-blue" 
                      style={{ width: '100%', padding: '10px', fontSize: '13px', fontWeight: 800 }}
                    >
                      🚀 Run Cloud Scheduler Trigger
                    </button>
                  </div>

                  {/* Right Column: Console Log output */}
                  <div style={{ display: 'flex', flexDirection: 'column', background: '#1e1e1e', borderRadius: '8px', padding: '16px', border: '2px solid #333', minHeight: '220px', overflow: 'hidden' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #333', paddingBottom: '8px', marginBottom: '12px' }}>
                      <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#888', fontWeight: 700 }}>LIVE GCP EVENT LOGS</span>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: automationLoading ? '#ffc800' : '#58cc02', animation: automationLoading ? 'pulse 1s infinite' : 'none' }}></span>
                    </div>

                    <div style={{ flexGrow: 1, fontFamily: 'monospace', fontSize: '11px', color: '#00ff00', textAlign: 'left', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {automationLogs.length === 0 ? (
                        <span style={{ color: '#888', fontStyle: 'italic' }}>Console idle. Click "Run Cloud Scheduler Trigger" to execute daily morning workflow...</span>
                      ) : (
                        automationLogs.map((log, index) => (
                          <div key={index} style={{ borderBottom: '1px solid #252525', paddingBottom: '4px' }}>
                            {log}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>


            </div>
          )}

          {/* ==================== PANEL: REPORT HAZARD ==================== */}
          {activeTab === 'hazard' && (
            <div className="tab-content active" style={{ display: 'block' }}>
              <h2>Report Road Safety Hazard</h2>
              <p>Upload a photo of double-parking, construction blocks, or road hazards. Guardian AI will analyze it to update risk scores in real-time.</p>

              <div className="panel-grid hazard-panel-grid">
                
                {/* Left: Drag and drop upload box */}
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '350px', border: '2.5px dashed var(--border-color)', cursor: 'pointer', position: 'relative' }}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                      handleHazardFileSelect(e.dataTransfer.files[0]);
                    }
                  }}
                >
                  <input 
                    type="file" 
                    ref={fileInputRef}
                    onChange={(e) => handleHazardFileSelect(e.target.files?.[0])}
                    accept="image/*"
                    style={{ display: 'none' }}
                  />

                  <div style={{ fontSize: '50px', marginBottom: '16px' }}>📸</div>
                  <h4 style={{ fontSize: '18px', marginBottom: '8px', color: 'var(--text-primary)' }}>Drag & Drop or Click to Upload Photo</h4>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '280px', textAlign: 'center', lineHeight: '1.4' }}>
                    Upload camera captures or near-miss photos. Gemini Multimodal vision performs safety analysis automatically.
                  </p>

                  {hazardPreviewUrl && (
                    <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'var(--card-bg)', borderRadius: 'inherit', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <img src={hazardPreviewUrl} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} alt="Preview"/>
                      <div style={{ position: 'absolute', bottom: '12px', background: 'rgba(0,0,0,0.7)', color: 'white', padding: '6px 14px', borderRadius: 'var(--radius-sm)', fontSize: '12px', fontWeight: 700 }}>
                        Click to change photo
                      </div>
                    </div>
                  )}
                </div>

                {/* Right: AI Vision detection results */}
                <div className="lingo-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '350px', textAlign: 'left' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', color: 'var(--text-primary)', textTransform: 'uppercase', marginBottom: '20px', fontWeight: 800, borderBottom: '2px solid var(--border-color)', paddingBottom: '10px' }}>
                      AI Vision Analysis Output
                    </h3>

                    {/* Idle State */}
                    {hazardAnalysisState === 'idle' && (
                      <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-secondary)' }}>
                        <span style={{ fontSize: '40px', display: 'block', marginBottom: '12px' }}>🔍</span>
                        <p style={{ fontWeight: 700, fontSize: '14px' }}>Awaiting photo upload for analysis...</p>
                      </div>
                    )}

                    {/* Loading State */}
                    {hazardAnalysisState === 'loading' && (
                      <div style={{ textAlign: 'center', padding: '40px 0' }}>
                        <div style={{ width: '40px', height: '40px', border: '4px solid var(--border-color)', borderTop: '4px solid var(--lingo-blue)', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px auto' }}></div>
                        <p style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>Guardian AI is performing Vision Analysis...</p>
                        <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>Identifying parking compliance and safety factors</p>
                      </div>
                    )}

                    {/* Result state */}
                    {hazardAnalysisState === 'result' && analyzedHazardData && (
                      <div>
                        <div 
                          style={{ 
                            backgroundColor: analyzedHazardData.severity_multiplier > 1.0 && analyzedHazardData.hazard_type !== 'SAFE_ZONE' ? "rgba(88,204,2,0.1)" : "rgba(28,176,246,0.1)", 
                            borderLeft: `4px solid ${analyzedHazardData.severity_multiplier > 1.0 && analyzedHazardData.hazard_type !== 'SAFE_ZONE' ? "var(--lingo-green)" : "var(--lingo-blue)"}`, 
                            padding: '12px 16px', 
                            borderRadius: '8px', 
                            marginBottom: '16px', 
                            fontSize: '13px', 
                            fontWeight: 700, 
                            color: analyzedHazardData.severity_multiplier > 1.0 && analyzedHazardData.hazard_type !== 'SAFE_ZONE' ? "var(--lingo-green-shadow)" : "var(--lingo-blue-shadow)" 
                          }}
                        >
                          {analyzedHazardData.severity_multiplier > 1.0 && analyzedHazardData.hazard_type !== 'SAFE_ZONE'
                            ? "✔ Gemini Multimodal Vision analysis successful!"
                            : "ℹ Vision simulation analysis complete (Offline fallback)."}
                        </div>

                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', fontWeight: 600, marginBottom: '16px' }}>
                          <tbody>
                            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                              <td style={{ padding: '8px 0', color: 'var(--text-secondary)' }}>Detected Hazard:</td>
                              <td style={{ padding: '8px 0', textAlign: 'right', color: 'var(--text-primary)' }}>
                                {analyzedHazardData.hazard_type}
                              </td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                              <td style={{ padding: '8px 0', color: 'var(--text-secondary)' }}>Risk Multiplier:</td>
                              <td style={{ padding: '8px 0', textAlign: 'right', color: 'var(--lingo-red)' }}>
                                +{analyzedHazardData.severity_multiplier}x
                              </td>
                            </tr>
                          </tbody>
                        </table>

                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600, lineHeight: 1.5, background: 'var(--bg-secondary)', padding: '12px', borderRadius: '8px', border: '1.5px solid var(--border-color)' }}>
                          {analyzedHazardData.description}
                        </p>
                      </div>
                    )}
                  </div>

                  {hazardAnalysisState === 'result' && (
                    <button 
                      onClick={submitHazardToDB}
                      className="btn-tactile lingo-btn green" 
                      style={{ width: '100%' }}
                    >
                      📁 Add Hazard to Safety Database
                    </button>
                  )}
                </div>

              </div>

              {/* History of hazards */}
              <div className="lingo-card" style={{ marginTop: '24px', textAlign: 'left' }}>
                <h4 style={{ fontSize: '16px', fontWeight: 800, marginBottom: '16px', color: 'var(--text-primary)' }}>
                  ⚠️ Active Safety Hazard Reports (This School Zone)
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {activeHazards.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '14px' }}>
                      No road hazards reported in this school zone yet.
                    </div>
                  ) : (
                    activeHazards.map(h => (
                      <div 
                        key={h.hazard_id} 
                        style={{ 
                          background: 'var(--bg-secondary)', 
                          border: '2px solid var(--border-color)', 
                          borderRadius: 'var(--radius-md)', 
                          padding: '14px 18px', 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center', 
                          boxShadow: '0 2px 0 var(--border-color)' 
                        }}
                      >
                        <div>
                          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700 }}>
                            {h.hazard_type}
                          </span>
                          <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px', margin: '4px 0 0 0' }}>
                            {h.description}
                          </p>
                        </div>
                        <span className="badge-risk high" style={{ marginLeft: '16px', flexShrink: 0 }}>
                          +{h.severity_multiplier}x
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ==================== PANEL: AI SAFETY BRIEFING ==================== */}
          {activeTab === 'briefing' && (
            <div className="tab-content active" style={{ display: 'block', textAlign: 'left' }}>
              <h2>PTA Weekly Safety Briefing</h2>
              <p>AI-generated digest coordinating crossing zone alerts, risk summaries, and community safety messages.</p>

              <div className="lingo-card" style={{ marginTop: '24px' }}>
                {isGeneratingNewsletter ? (
                  <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                    <div style={{ width: '48px', height: '48px', border: '4px solid var(--border-color)', borderTop: '4px solid var(--lingo-purple)', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 20px auto' }}></div>
                    <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>Compiling Safety Publication</h3>
                    <p style={{ maxWidth: '480px', margin: '8px auto 0 auto', fontSize: '14px', lineHeight: '1.5', color: 'var(--text-secondary)' }}>
                      Guardian AI is synthesizing recent traffic hazard reports, active guardian rosters, and safety spikes to draft your community bulletin...
                    </p>
                  </div>
                ) : !newsletterHtml ? (
                  <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
                    <span style={{ fontSize: '48px', display: 'block', marginBottom: '16px' }}>🦉</span>
                    <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>No Briefing Generated Yet</h3>
                    <p style={{ maxWidth: '480px', margin: '8px auto 20px auto', fontSize: '14px', lineHeight: '1.5' }}>
                      {user.role === 'super_admin' 
                        ? "You haven't generated a briefing for this school zone this week. Compile your first AI-powered PTA Safety Briefing using the button below!"
                        : "The school administrator has not published a safety briefing for this week yet. Please check back later!"}
                    </p>
                    {user.role === 'super_admin' && (
                      <button 
                        onClick={handleGenerateNewsletter} 
                        className="btn-tactile btn-blue" 
                        style={{ backgroundColor: 'var(--lingo-purple)', boxShadow: '0 4px 0 var(--lingo-purple-shadow)' }}
                      >
                        ✨ Generate PTA Safety Briefing (AI)
                      </button>
                    )}
                  </div>
                ) : (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
                      <h3 style={{ margin: 0 }}>Latest Safety Publication</h3>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          onClick={() => {
                            navigator.clipboard.writeText(newsletterHtml);
                            alert('PTA Safety Newsletter HTML code copied to clipboard!');
                          }}
                          className="btn-tactile btn-blue"
                          style={{ padding: '8px 16px', fontSize: '12px' }}
                        >
                          📋 Copy HTML
                        </button>
                        <button 
                          onClick={() => window.print()}
                          className="btn-tactile btn-blue"
                          style={{ padding: '8px 16px', fontSize: '12px' }}
                        >
                          🖨️ Print Briefing
                        </button>
                        {user.role === 'super_admin' && (
                          <button 
                            onClick={handleGenerateNewsletter}
                            className="btn-tactile btn-green"
                            style={{ padding: '8px 16px', fontSize: '12px', background: 'var(--lingo-purple)', border: 'none', boxShadow: '0 4px 0 var(--lingo-purple-shadow)' }}
                          >
                            🔄 Regenerate (AI)
                          </button>
                        )}
                      </div>
                    </div>
                    
                    <div 
                      style={{ border: '2px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '24px', background: 'var(--bg-secondary)', overflowX: 'auto', maxWidth: '100%', minHeight: '300px' }}
                      dangerouslySetInnerHTML={{ __html: newsletterHtml }}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}

/* ==========================================================================
   REACT MAP SUB-COMPONENT (Real Leaflet Map)
   ========================================================================== */
const MapComponent = ({ 
  latitude, 
  longitude, 
  schoolName, 
  historicalIncidents, 
  level,
  theme,
  activeHazards 
}: { 
  latitude: number; 
  longitude: number; 
  schoolName: string; 
  historicalIncidents: number; 
  level: string;
  theme: string;
  activeHazards: any[];
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersGroupRef = useRef<any>(null);

  useEffect(() => {
    const L = (window as any).L;
    if (!L || !mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapContainerRef.current, {
        center: [latitude, longitude],
        zoom: 15,
        zoomControl: true,
        attributionControl: false
      });

      const tileUrl = theme === 'dark' 
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';

      L.tileLayer(tileUrl, {
        maxZoom: 19
      }).addTo(mapInstanceRef.current);

      markersGroupRef.current = L.featureGroup().addTo(mapInstanceRef.current);
    }

    const map = mapInstanceRef.current;
    map.setView([latitude, longitude], 15);

    // Update tile layer based on active theme
    map.eachLayer((layer: any) => {
      if (layer instanceof L.TileLayer) {
        const tileUrl = theme === 'dark' 
          ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
          : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
        layer.setUrl(tileUrl);
      }
    });

    if (markersGroupRef.current) {
      markersGroupRef.current.clearLayers();
    }

    let safetyColor = '#58cc02';
    if (level === 'MEDIUM') safetyColor = '#ffc800';
    if (level === 'HIGH') safetyColor = '#ff4b4b';

    // Concentric Safety Buffer
    const safetyCircle = L.circle([latitude, longitude], {
      color: safetyColor,
      fillColor: safetyColor,
      fillOpacity: 0.12,
      radius: 300,
      dashArray: '5, 10'
    }).addTo(markersGroupRef.current);

    safetyCircle.bindPopup(`<strong>${schoolName} Safety Buffer</strong><br/>Radius: 300m<br/>Alert Level: ${level} RISK`);

    // School Marker Icon
    const schoolIcon = L.divIcon({
      html: `<div style="font-size: 26px; line-height: 1; text-align: center; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.35));">🏫</div>`,
      className: 'custom-leaflet-icon',
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    L.marker([latitude, longitude], { icon: schoolIcon })
      .addTo(markersGroupRef.current)
      .bindPopup(`<strong>${schoolName}</strong><br/>Historical Incident Rate: ${historicalIncidents} crashes`);

    // Historical Incident Markers (Concentric Scatter)
    const limit = Math.min(historicalIncidents, 6);
    for (let i = 0; i < limit; i++) {
      const angle = (i * (2 * Math.PI) / 6) + 0.5;
      const radiusOffset = 0.0012 + (i * 0.0003) % 0.0008;
      const incidentLat = latitude + radiusOffset * Math.sin(angle);
      const incidentLng = longitude + radiusOffset * Math.cos(angle);

      const collisionIcon = L.divIcon({
        html: `<div style="font-size: 20px; line-height: 1; text-align: center; animation: pulse 2s infinite alternate;">💥</div>`,
        className: 'custom-leaflet-icon',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      L.marker([incidentLat, incidentLng], { icon: collisionIcon })
        .addTo(markersGroupRef.current)
        .bindPopup(`<strong>Spatial Collision Record</strong><br/>Location: Buffer zone<br/>Category: Vehicle vs Pedestrian`);
    }

    // Active Hazard Report Markers
    if (activeHazards && activeHazards.length > 0) {
      activeHazards.forEach((hazard, idx) => {
        const angle = idx * 1.5;
        const radiusOffset = 0.0008;
        const hazardLat = latitude + radiusOffset * Math.sin(angle);
        const hazardLng = longitude + radiusOffset * Math.cos(angle);

        const hazardIcon = L.divIcon({
          html: `<div style="font-size: 22px; line-height: 1; text-align: center; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.25));">⚠️</div>`,
          className: 'custom-leaflet-icon',
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });

        L.marker([hazardLat, hazardLng], { icon: hazardIcon })
          .addTo(markersGroupRef.current)
          .bindPopup(`<strong>Active Hazard Report</strong><br/>Type: ${hazard.hazard_type}<br/>Multiplier: +${hazard.severity_multiplier}x<br/>Description: ${hazard.description}`);
      });
    }

    // Force rendering sizes check
    setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 100);

    // Cleanup hook on dependencies change and unmount
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };

  }, [latitude, longitude, schoolName, historicalIncidents, level, theme, activeHazards]);

  return (
    <div 
      ref={mapContainerRef} 
      className="map-leaflet-container" 
      style={{ 
        width: '100%', 
        height: '100%',
        minHeight: '340px',
        flexGrow: 1, 
        borderRadius: '0 0 var(--radius-md) var(--radius-md)', 
        border: 'none',
        overflow: 'hidden',
        position: 'relative',
        zIndex: 5
      }} 
    />
  );
};

export default App;
