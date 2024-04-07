import React, { useState, useEffect, useRef } from 'react';
import { Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const OnlineGame = () => {

  const PADDLE_WIDTH = 10;
  const PADDLE_HEIGHT = 75;
  const [players, setPlayers] = useState([
    { paddleY: 0, upPressed: false, downPressed: false, score: 0 },
    { paddleY: 0, upPressed: false, downPressed: false, score: 0 },
  ]);
  const [ball, setBall] = useState({ x: 0, y: 0, r: 10 });
  
  const [playerNum, setPlayerNum] = useState(0);
  const [gameStarted, setGameStarted] = useState(false);
  const playersRef = useRef(players);
  const playerNumRef = useRef(playerNum);
  const navigate = useNavigate();
 

  const startGame = () => {
	
	const idd = localStorage.getItem('friendID');
    const websocket = new WebSocket('ws://localhost:8000/ws/private_game/' + idd + '/?token=' + localStorage.getItem('Token'));
	localStorage.removeItem('friendID');
    websocket.onopen = () => {
      console.log('WebSocket connection opened');
    };

    websocket.onclose = () => {
      console.log('WebSocket connection closed');
    };

    websocket.onerror = (event) => {
      console.error('WebSocket error:', event);
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'playerNum') {
        
        setPlayerNum(message.playerNum);
		console.log('Received playerNum:', message);
		// websocket.send(
		// 	JSON.stringify({
		// 		type: 'canvas_size',
		// 		playerId: playerIDRef.current,
		// 		playerNum: playerNumRef.current,
		// 		canvasWidth: window.innerWidth,
		// 		canvasHeight: window.innerHeight,
		// 	})
		// );
      } else if (message.type === 'game_start') {
        console.log('Received game_start:', message);
        setGameStarted(true);
      } else if (message.type === 'game_update') {
        setBall({ x: message.x, y: message.y });
		setPlayers([
			{ ...players[0], paddleY: message.player1_paddleY, score: message.player1_score },
			{ ...players[1], paddleY: message.player2_paddleY, score: message.player2_score },
		  ]);
		if (websocket) {
			websocket.send(
				JSON.stringify({
					type: 'game_update',
					playerNum: playerNumRef.current,
					upPressed: playersRef.current[0].upPressed,
					downPressed: playersRef.current[0].downPressed,
				})
				);
			
		}
        
      } else if (message.type === 'game_end') {
        console.log('Received game_over:', message);
        if (websocket) {
          websocket.close();
        }
        setTimeout(() => {
          handleBack();
        }, 2000);
      }
    };
  };

  useEffect(() => {
    document.addEventListener('keydown', keyDownHandler);
    document.addEventListener('keyup', keyUpHandler);

    return () => {
      document.removeEventListener('keydown', keyDownHandler);
      document.removeEventListener('keyup', keyUpHandler);
    };
  }, []);

  useEffect(() => {
    playerNumRef.current = playerNum;
    }	, [playerNum]);

  useEffect(() => {
    playersRef.current = players;
  }, [players]);

  const keyDownHandler = (e) => {
	if (e.code === 'ArrowUp') {
	  setPlayers((prevPlayers) => [{ ...prevPlayers[0], upPressed: true }, prevPlayers[1]]);
	  console.log('up pressed');
	} else if (e.code === 'ArrowDown') {
	  setPlayers((prevPlayers) => [{ ...prevPlayers[0], downPressed: true }, prevPlayers[1]]);
	  console.log('down pressed');
	}
  };
  
  const keyUpHandler = (e) => {
	if (e.code === 'ArrowUp') {
	  setPlayers((prevPlayers) => [{ ...prevPlayers[0], upPressed: false }, prevPlayers[1]]);
	  console.log('up released');
	} else if (e.code === 'ArrowDown') {
	  setPlayers((prevPlayers) => [{ ...prevPlayers[0], downPressed: false }, prevPlayers[1]]);
	  console.log('down released');
	}
  };

  const handleBack = () => {
    navigate('/'); // Navigiere zur Startseite, wenn der "Zurück"-Button geklickt wird
};
  
  return (
    <div style={{ position: 'relative', height: 480 + 'px', width: 480 + 'px' }}>
      {!gameStarted ? (
        <div className="d-flex justify-content-center align-items-center" style={{ height: '100%' }}>
          <Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" onClick={startGame}>start game</Button>
          <Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" onClick={handleBack}>back to menu</Button>
        </div>
      ) : (
        <>
          {/* Ball */}
          <div
            className="ball"
            style={{
              position: 'absolute',
              top: `${ball.y}px`,
              left: `${ball.x}px`,
              width: `${ball.r * 2}px`,
              height: `${ball.r * 2}px`,
              borderRadius: '50%',
              backgroundColor: '#0095DD',
            }}
          ></div>
          {/* Paddle 1 */}
          <div
            className="paddle"
            style={{
              position: 'absolute',
              top: `${players[0].paddleY}px`,
              left: '0px',
              width: `${PADDLE_WIDTH}px`, // Breite des Paddels
              height: `${PADDLE_HEIGHT}px`, // Höhe des Paddels
              backgroundColor: '#0095DD',
            }}
          ></div>
          {/* Paddle 2 */}
          <div
            className="paddle"
            style={{ position: 'absolute', top: `${players[1].paddleY}px`, right: '0px', width: `${PADDLE_WIDTH}px`, height: `${PADDLE_HEIGHT}px`, backgroundColor: '#0095DD',}}
          ></div>
		  {/* Score */}
		<div
			style={{
				position: 'fixed',
				top: '10px',
				left: '50%',
				transform: 'translateX(-50%)',
				color: '#000',
				fontSize: '20px',
				fontWeight: 'bold',
			}}
		>
			{players[0].score} : {players[1].score}
		</div>
        </>
      )}
    </div>
  );
};

export default OnlineGame;
