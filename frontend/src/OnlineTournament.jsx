import React, { useState, useEffect } from 'react';
/* eslint-disable */
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';

import { Button, Card, Container } from 'react-bootstrap';


const OnlineTournament = (props) => {
	const [notification, setNotification] = useState(null);
	const backendURL = 'http://localhost:8000/tournaments/'
	const [tournaments, setTournaments] = useState([]);
	const [userData, setUserData] = useState({});
	const navigate = useNavigate();
	const {socket} = props;
	useEffect(() => {
		fetchTournaments();
	}, []);

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

	useEffect(() => {
		fetchUserData();
	}, []);

	const fetchUserData = () => {
		const backendURL = 'http://localhost:8000/users/';
    	const userId = localStorage.getItem('id');
		const requestURL = `${backendURL}${userId}/`;
		fetch(requestURL, {
			method: 'GET',
			headers: {
			  'Content-Type': 'application/json	',	
			  'Authorization': `Token ${localStorage.getItem('Token')}`
			},
			})
			.then(response => response.json())		
			.then(data => {
				setUserData(data);
			})
			.catch((error) => {
				console.error('Error:', error);
			}
		);
	};	

	const fetchTournaments = () => {

		fetch(backendURL, {
			method: 'GET',
			headers: {
			  'Content-Type': 'application/json',
			  'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
			},
		  })
		  .then(response => response.json())
		  .then(data => {
			setTournaments(data);
		  })
		  .catch((error) => {
			console.error('Error:', error);
		  });

	};

	const createTournament = () => {	
		fetch(backendURL, {
			method: 'POST',
			headers: {
			  'Content-Type': 'application/json',
			  'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
			},
		  })
		  .then(response => response.json())
		  .then(data => {
			window.location.reload();
		  })
		  .catch((error) => {
			console.error('Error:', error);
		  });
	}

	const unregisterTournamet = () => {
		fetch(backendURL, {
			method: 'DELETE',
			headers: {
			  'Content-Type': 'application/json',
			  'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
			},
		  })
		  .then(response => {
			window.location.reload();
		  })

		  .then(data => {
			
		  })
		  .catch((error) => {
			console.error('Error:', error);
		  });
		}

	const registerToAnTournament = (tournamentId) => {
		fetch(`http://localhost:8000/tournaments/register/${tournamentId}/`, {
			method: 'PUT',
			headers: {
			  'Content-Type': 'application	json',
			  'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
			},
		  })
		  .then(response => {
			window.location.reload();
		  })

		  .then(data => {
			
		  })
		  .catch((error) => {

			console.error('Error:', error);
		  });
		}
		const handleBack = () => {
  
     
			navigate('/'); // Navigiere zur Startseite, wenn der "Zurück"-Button geklickt wird
			
		  };
		
	return (
		<Container>
			{notification && <div className="notification" style={{position: 'fixed', top: 0, right: 0, backgroundColor: 'lightblue', padding: '10px'}}>{notification.message}</div>}
			<h1>Online Tournaments</h1>
			{userData && userData.profile && userData.profile.tournament ? (
				<Card className="mb-3">
					<Card.Body>
					<Card.Title>{userData.profile.tournament.name}</Card.Title>
					<Card.Text>Registered</Card.Text>
					<Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="danger" onClick={unregisterTournamet}>Unregister</Button>
					</Card.Body>
				</Card>
			) : (
			tournaments.length > 0 ? (
				tournaments.map((tournament) => (
				<Card key={tournament.id} className="mb-3">
					<Card.Body>
					<Card.Title>{tournament.name}</Card.Title>
					{tournament.isFull ? (
						<Card.Text>The tournament is full.</Card.Text>
					) : (
						<Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" onClick={() => registerToAnTournament(tournament.id)}>Register</Button>
					)}
				</Card.Body>
				</Card>
				))
			) : (
				<p>No tournaments available.</p>
			)
			)}
			<Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="primary" className="mr-2" onClick={createTournament}>Create Tournament</Button>
			<Button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} variant="secondary" onClick={handleBack}>Back to Menu</Button>
		</Container>
	);
};

export default OnlineTournament;