import React, { useState } from 'react';
import './css/TournamentReg.css';

function TournamentReg({ onSubmit }) {
  const [step, setStep] = useState(1);
  const [playerCount, setPlayerCount] = useState('');
  const [playerNames, setPlayerNames] = useState([]);

  const handlePlayerCountSubmit = (event) => {
    event.preventDefault();
    if (playerCount >= 2 && playerCount <= 8) {
      setPlayerNames(Array(parseInt(playerCount)).fill(''));
      setStep(2);
    } else {
      alert('Please enter a valid player count between 2 and 8.');
    }
  };

  const handlePlayerNamesSubmit = (event) => {
    event.preventDefault();
    onSubmit(playerNames.slice(0, playerCount));
  };

  const handlePlayerNameChange = (index, event) => {
    const newPlayerNames = [...playerNames];
    newPlayerNames[index] = event.target.value;
    setPlayerNames(newPlayerNames);
  };

  return (
    <div>
      <div className="form-container">
        {step === 1 && (
          <form onSubmit={handlePlayerCountSubmit}>
            <label>
              How many players will participate?
              <input
                type="number"
                min="2"
                max="8"
                value={playerCount}
                onChange={(event) => setPlayerCount(event.target.value)}
                required
              />
            </label>
            <button type="submit">Next</button>
          </form>
        )}
      </div>
      <div className="form-container">
        {step === 2 && (
          <form onSubmit={handlePlayerNamesSubmit}>
            {playerNames.map((name, index) => (
              <label key={index}>
                Player {index + 1} Name:
                <input
                  type="text"
                  value={name}
                  onChange={(event) => handlePlayerNameChange(index, event)}
                  required
                />
              </label>
            ))}
            <button type="submit">Start Tournament</button>
          </form>
        )}
      </div>
    </div>
  );
}

export default TournamentReg;
