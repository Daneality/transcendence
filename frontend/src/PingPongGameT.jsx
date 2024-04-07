import React, { useState, useEffect, useRef } from 'react';
/* eslint-disable */
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import './css/PingPongGame.css';

const PingPongGameT = ({ player1, player2}) => {
  const [ballPosition, setBallPosition] = useState({ x: window.innerWidth / 2, y: window.innerHeight / 2 }); // Ball außerhalb des Bildschirms platzieren
  const [ballVelocity, setBallVelocity] = useState({ xx: 0, y: 0}); // Ballgeschwindigkeit auf 0 setzen
  const [leftpaddlePosition, leftsetPaddlePosition] = useState(window.innerHeight / 2 - 50);
  const [rightpaddlePosition, rightsetPaddlePosition] = useState(window.innerHeight / 2 - 50);
  const [gameStarted, setGameStarted] = useState(false);
  const [countdown, setCountdown] = useState(3); // Countdown-Wert
  const [score, setScore] = useState({left: 0, right: 0});
  const [leftscored, setleftScore] = useState(false);
  const [rightscored, setrightScore] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [winner, setWinner] = useState(null);

  const leftpaddleRef = useRef(null);
  const rightpaddleRef = useRef(null);

  const navigate = useNavigate();
 /* check game over*/
  const checkGameOver = () => {
    if (score.left >=2) {
      setGameOver(true);
      setWinner(player1);
    } else if (score.right >=2){
      setWinner(player2)
    }
  };

  useEffect(() => {
    if (gameOver) {
      if (!localStorage.getItem('winner_1')) {
        localStorage.setItem('winner_1', winner);
       }
       else if (!localStorage.getItem('winner_2')) {
        localStorage.setItem('winner_2', winner);
       } 
       else {
        localStorage.setItem('t_winner', winner);
       }
        // Speichern des Gewinners im Local Storage
      window.location.reload(); // Seite neu laden, um das Spiel zurückzusetzen
    }
  }, [gameOver, winner]);

  useEffect(() => {
    checkGameOver();
  }, [score]);

  /* score, countdown */
  useEffect(() => {
    if (gameStarted) return;
    if (leftscored) {
      setScore((prevScore) => ({...prevScore, right: prevScore.right + 1}));
      setleftScore(false);
    }
    if (rightscored) {
      setScore((prevScore) => ({...prevScore, left: prevScore.left + 1}));
      setrightScore(false);
    }
    const countdownInterval = setInterval(() => {
      setCountdown((prevCountdown) => prevCountdown - 1);
    }, 1000); // Jede Sekunde

    if (countdown === 0) {
      setGameStarted(true);
      setCountdown(3);
    }
    return () => clearInterval(countdownInterval);
  }, [gameStarted, countdown, rightscored, leftscored]);
/* countdown */
  useEffect(() => {
    if (gameStarted) return;
    const gameTimeout = setTimeout(() => {
      setBallVelocity({ x: 3, y: 3 });
    }, 3000);
    return () => clearTimeout(gameTimeout);
  }, [gameStarted]);
/* paddle position*/
  useEffect(() => {
    const handleKeyPress = (event) => {
      if (event.key === 'w' && leftpaddlePosition > 0) {
        leftsetPaddlePosition(leftpaddlePosition - 60);
      } else if (event.key === 's' && leftpaddlePosition < window.innerHeight - 100) {
        leftsetPaddlePosition(leftpaddlePosition + 60);
      }
      else if (event.key === 'ArrowUp' && rightpaddlePosition > 0) {
      rightsetPaddlePosition(rightpaddlePosition - 60);
    } else if (event.key === 'ArrowDown' && rightpaddlePosition < window.innerHeight - 100) {
      rightsetPaddlePosition(rightpaddlePosition + 60);
    }
    };
    window.addEventListener('keydown', handleKeyPress);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };

  }, [leftpaddlePosition, rightpaddlePosition]);


  useEffect(() => {
    const updateGame = () => {
      if (gameOver || !gameStarted) return;
      setBallPosition((prevPosition) => {
        let nextX = prevPosition.x + ballVelocity.x;
        let nextY = prevPosition.y + ballVelocity.y;
        if (
          nextX <= 20 &&
          nextY + 20 >= leftpaddlePosition &&
          nextY <= leftpaddlePosition + 100
        ) {
          const newVelocityX = -ballVelocity.x * 1.05;
          const newVelocityY = (ballVelocity.y + Math.random() * 2 - 1) * 1.05; // zufällige Abweichung in y-Richtung
          setBallVelocity({ x: newVelocityX, y: newVelocityY });
        }
        else if (
          nextX >= window.innerWidth - 40 && // Überprüfen Sie, ob der Ball die Nähe des rechten Paddels erreicht hat
          nextY + 20 >= rightpaddlePosition && // Überprüfen Sie, ob der Ball die Oberkante des rechten Paddels erreicht hat
          nextY <= rightpaddlePosition + 100 // Überprüfen Sie, ob der Ball die Unterkante des rechten Paddels erreicht hat
        ) {
          // Kollision mit dem rechten Paddel, erhöhen Sie die Geschwindigkeit des Balls
            // Erhöhen Sie die Geschwindigkeit in x-Richtung um 5%
            const newVelocityX = -ballVelocity.x * 1.05; // Umkehrung der horizontalen Geschwindigkeit und Erhöhung um 5%
            // Zufällige Abweichung in y-Richtung und Erhöhung um 5%
            const newVelocityY = (ballVelocity.y + Math.random() * 2 - 1) * 1.05; 
            setBallVelocity({x: newVelocityX, y: newVelocityY});
        }
        
        // Check if the ball hits the boundaries
        else if (nextX <= 0) {
          setGameStarted(false);
          setBallPosition({ x: window.innerWidth / 2, y: window.innerHeight / 2 });
          setleftScore(true);
        }
        else if (nextX >= window.innerWidth - 20) {
          setGameStarted(false);
          setBallPosition({ x: window.innerWidth / 2, y: window.innerHeight / 2 });
          setrightScore(true);
        }
        else if (nextY <= 0 || nextY >= window.innerHeight - 20) {
          const newVelocityX = ballVelocity.x + Math.random() * 2 - 1; // zufällige Abweichung in x-Richtung
          const newVelocityY = -ballVelocity.y;
          setBallVelocity({ x: newVelocityX, y: newVelocityY });
          nextY = nextY <= 0 ? 0 : window.innerHeight - 20; // Keep the ball inside the boundaries
        }
        return { x: nextX, y: nextY };
      });
    };

    const gameInterval = setInterval(updateGame, 5);

    return () => {
      clearInterval(gameInterval);
    };
  }, [ballVelocity, leftpaddlePosition, rightpaddlePosition, gameStarted, gameOver]);

  const handleBack = () => {
    navigate('/'); // Navigiere zur Startseite, wenn der "Zurück"-Button geklickt wird
  };

  const restartGame = () => {
    setGameOver(false);
    setScore({left: 0, right: 0});
    setCountdown(3);
    // setGameStarted(true);
    // setBallVelocity({ x: 3, y: 3 });
  };

  return (
    <div className="ball-game-container">
      {!gameOver && (<button className="back-button" onClick={handleBack}>menu</button>)}
      <div className='button-container'>
      {gameOver && (<button className='backtomenu-button' onClick={handleBack}>menu</button>)}
      {gameOver && (<button className='restart-button' onClick={restartGame}>restart</button>)}
      </div>
      <div className="score-display">{score.left} : {score.right}</div>
      <div className="left-player-name">{player2}</div>
        <div className="right-player-name">{player1}</div>
      <div className="ball" style={{ top: ballPosition.y + 'px', left: ballPosition.x + 'px' }}></div>
      {!gameStarted && !gameOver && (
        <div className="countdown-display">{countdown}</div>
      )}
      <div ref={leftpaddleRef} className="paddle left-paddle" style={{ top: leftpaddlePosition + 'px' }}></div>
      <div ref={rightpaddleRef} className="paddle right-paddle" style={{ top: rightpaddlePosition + 'px' }}></div>
    </div>
  );
};

export default PingPongGameT;
