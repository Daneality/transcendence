
import { BrowserRouter as Router, Routes, Route, Link} from 'react-router-dom';
import PingPongGame from './PingPongGame';
import Tournament from './Tournament';
import Chat from './Chat';
import './css/App.css';
import Login from './Login';
import Dashboard from './Dashboard';
import OnlineGame from './OnlineGame';
import React, { useState, useEffect } from 'react';
import OnlineTournament from './OnlineTournament';
import OnlineGameM from './OnlineGameM';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [notification, setNotification] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem('Token'));
  }, []);

  useEffect(() => {
    if (!isLoggedIn) return;
    const newSocket = new WebSocket('ws://localhost:8000/ws/notification/?token=' + localStorage.getItem('Token'));
    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [isLoggedIn]);

  useEffect(() => {
    if (socket == null) return;

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      console.log(data);
      setNotification(data);
      setTimeout(() => {
        setNotification(null);
      }, 5000);
    };
  }, [socket]);


  return (
    <Router>
      <div className="App">
      {notification && <div className="notification" style={{position: 'fixed', top: 0, right: 0, backgroundColor: 'lightblue', padding: '10px'}}>{notification.message}</div>}
        <Routes>
          <Route
            path="/"
            element={
              <>
                <header>
                  <h1>ft_transcendence</h1>
                </header>
                <div className="start-page d-flex justify-content-center align-items-center vh-100">
                  <div className="button-container">
                  {isLoggedIn ? (
                      <Link to={`/dashboard/${localStorage.getItem('id')}/`}>
                        <button className="btn btn-primary m-2" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}}>
                          profile
                        </button>
                      </Link>
                    ) : (
                      <Link to="/login">
                        <button className="btn btn-primary m-2" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}}>
                          Login
                        </button>
                      </Link>
                    )}
                    <Link to="/game">
                      <button className="btn btn-primary m-2" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}}>
                        local game
                      </button>
                    </Link>
                    {isLoggedIn && (<Link to="/OnlineGameM">
                      <button className="btn btn-primary m-2" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}}>
                        online game
                      </button>
                    </Link>)}
                    <Link to="/tournament">
                      <button className="btn btn-primary m-2" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}}>
                        local tournament
                      </button>
                    </Link>
                    {isLoggedIn && (<Link to="/onlineTournament">
                      <button className="btn btn-primary m-2" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}}>
                        online tournament
                      </button>
                    </Link>)}
                   
                  </div>
                </div>
              </>
            }
          />
          <Route path="/game" element={<PingPongGame socket={socket} />} />
          <Route path='/tournament' element={<Tournament socket={socket} />} />
          <Route path="/login" element={<Login socket={socket} />} />
          <Route path="/dashboard/:id" element={<Dashboard socket={socket} />} />
          <Route path="/chat" element={<Chat socket={socket} />} />
          <Route path="/OnlineGame" element={<OnlineGame socket={socket} />} />
          <Route path='/onlineTournament' element={<OnlineTournament socket={socket} />} />
          <Route path="/OnlineGameM" element={<OnlineGameM socket={socket} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
