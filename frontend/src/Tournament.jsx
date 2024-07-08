import React, { useState, useEffect } from 'react';
import { Button, Form } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import PingPongGameT from './PingPongGameT'; // Importieren der Game-Komponente


const Tournament = () => {
  const [showNewTournamentForm, setShowNewTournamentForm] = useState(false);
  const [playerNames, setPlayerNames] = useState(['', '', '', '']);
  const [tournamentStarted, setTournamentStarted] = useState(false);
  const [playerPairs, setPlayerPairs] = useState([]);
  const [currentPairIndex, setCurrentPairIndex] = useState(0);
  const [gameStarted, setGameStarted] = useState(false); // Zustand für Spielstart
  const [winner, setWinner] = useState(null)
  const navigate = useNavigate();

  useEffect(() => {
    const tournamentStatus = localStorage.getItem('tournament');
    if (tournamentStatus === 'true') {
      const storedPlayerNames = ['player1Name', 'player2Name', 'player3Name', 'player4Name']
        .map((key) => localStorage.getItem(key));
      setPlayerNames(storedPlayerNames);
      setTournamentStarted(true);
      if (localStorage.getItem('playerPairs')) {
        setPlayerPairs(JSON.parse(localStorage.getItem('playerPairs')));
      } else {
        generatePlayerPairs(storedPlayerNames);
      }
    }
  }, []);

  useEffect(() => {
    if (localStorage.getItem('winner_1') && !localStorage.getItem('winner_2')) {
      setCurrentPairIndex(currentPairIndex + 1);
      setGameStarted(false);
    }
    else if (localStorage.getItem('winner_2') && !localStorage.getItem('t_winner')) {
      const pairs = [localStorage.getItem('winner_1'), localStorage.getItem('winner_2')];
      setPlayerPairs([pairs]);
      setGameStarted(false);
      setCurrentPairIndex(0);
    }
    else if (localStorage.getItem('t_winner')) {
      setWinner(localStorage.getItem('t_winner'));
      setGameStarted(false);
    }
    // eslint-disable-next-line
    }, []);

  const handleBack = () => {
    navigate('/');
  };

  const handleChange = (index, name) => {
    const updatedPlayerNames = [...playerNames];
    updatedPlayerNames[index] = name;
    setPlayerNames(updatedPlayerNames);
  };

  const handleSubmitNewTournament = (e) => {
    e.preventDefault();
    localStorage.setItem('player1Name', playerNames[0]);
    localStorage.setItem('player2Name', playerNames[1]);
    localStorage.setItem('player3Name', playerNames[2]);
    localStorage.setItem('player4Name', playerNames[3]);
    localStorage.setItem('tournament', true);
    setTournamentStarted(true);
    localStorage.removeItem('winner_1');
    localStorage.removeItem('winner_2'); 
    localStorage.removeItem('t_winner');
    setWinner(null);
    setCurrentPairIndex(0);
    if (!localStorage.getItem('playerPairs')) {
      generatePlayerPairs(playerNames);
    }
  };

  const handleStartGame = () => {
    setGameStarted(true); // Spielstart setzen
  };

  const generatePlayerPairs = (players) => {
    const shuffledPlayers = [...players].sort(() => Math.random() - 0.5);
    const pairs = [];
    for (let i = 0; i < shuffledPlayers.length; i += 2) {
      pairs.push([shuffledPlayers[i], shuffledPlayers[i + 1]]);
    }
    setPlayerPairs(pairs);
    localStorage.setItem('playerPairs', JSON.stringify(pairs));
  };

  const endT = () => {
    localStorage.removeItem('winner_1');
    localStorage.removeItem('winner_2'); 
    localStorage.removeItem('t_winner');
    localStorage.setItem('tournament', false);
    localStorage.removeItem('playerPairs');
    localStorage.removeItem('player1Name');
    localStorage.removeItem('player2Name');
    localStorage.removeItem('player3Name');
    localStorage.removeItem('player4Name');
    setTournamentStarted(false);
    setWinner(null);
    setCurrentPairIndex(0);
    navigate('/');
  }

  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="text-center">
        {tournamentStarted ? (
          <>
            {winner ? (
              <div>
                <h2>YOU WON!</h2>
                <p>{winner}</p>
                <Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" onClick={endT}>kewl</Button>
              </div>
            ) : (
              <>
                {gameStarted ? (
                  <PingPongGameT
                    player1={playerPairs[currentPairIndex][0]}
                    player2={playerPairs[currentPairIndex][1]}
                  />
                ) : (
                  <div>
                    <h2>  {localStorage.getItem('winner_1') && localStorage.getItem('winner_2') ? 'Final' : `Match ${currentPairIndex + 1}`}</h2>
                    <p>{playerPairs[currentPairIndex][0]} VS {playerPairs[currentPairIndex][1]}</p>
                    <Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" onClick={handleStartGame}>start game</Button>
                  </div>
                )}
              </>
            )}
            {!gameStarted && !winner && (
              <Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" size="lg" onClick={() => { localStorage.removeItem('tournament'); localStorage.removeItem('playerPairs'); setTournamentStarted(false); }}>new tournament</Button>
            )}
          </>
        ) : (
          <>
            {showNewTournamentForm ? (
              <Form onSubmit={handleSubmitNewTournament}>
                {playerNames.map((name, index) => (
                  <Form.Group key={index}>
                    <Form.Label>Player {index + 1} Name:</Form.Label>
                    <Form.Control
                      type="text"
                      value={name}
                      onChange={(e) => handleChange(index, e.target.value)}
                      required
                    />
                  </Form.Group>
                ))}
                <Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" type="submit">
                  start tournament
                </Button>
              </Form>
            ) : (
              <Button
                variant="primary"
                className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}}
                onClick={() => setShowNewTournamentForm(true)}>
                new tournament
              </Button>
            )}
          </>
        )}
        {!gameStarted && !winner && (
          <Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" size="lg" onClick={handleBack}>
            back to menu
          </Button>
        )}
      </div>
    </div>
  );
};

export default Tournament;
