import React, { useState } from 'react';
/* eslint-disable */
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, Form } from 'react-router-dom';
import Dashboard from './Dashboard';
import './css/Login.css';
import Cookies from 'js-cookie';


function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [alias, setAlias] = useState('');
  const [registering, setRegistering] = useState(false);

  const navigate = useNavigate();

  const handleUsernameChange = (event) => {
    setUsername(event.target.value);
  };

  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
  };

  const handleEmailChange = (event) => {
	setEmail(event.target.value);
  };
  
  const handleAliasChange = (event) => {
	setAlias(event.target.value);
  };
  

const handleLogin = () => {
	if (username.trim() === '' || password.trim() === '') {
		alert('Please enter username and password');
		return;
	  }

	  const backendURL = 'http://localhost:8000/login/';
  fetch(backendURL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })
  .then(response => {
	if (response.ok) {
	  // Die Antwort des Servers in JSON umwandeln
	  return response.json();
	} else {
	  // Wenn die Antwort nicht ok ist, zeige eine Fehlermeldung an
	  throw new Error('Es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.');
	}
  })
  .then(data => {
	// Den Token aus der Antwort extrahieren
	const token = data.token;
	const id = data.user.id;

	// Den Token lokal speichern
	localStorage.setItem('Token', token);
	Cookies.set('Token', token);
	localStorage.setItem('id', id);

	// Weiterleiten oder andere Aktionen ausführen
	navigate(`/dashboard/${id}/`);
  })
  .catch(error => {
    // Fehlerbehandlung, falls ein Fehler auftritt
    console.error('Fehler beim Senden der Registrierungsdaten:', error);
    alert(error.message); // Fehlermeldung anzeigen
  });

  
};


const handleRegister = () => {
	// Speichere die eingegebenen Daten lokal
	if (username.trim() === '' || password.trim() === '' || email.trim() === '' || alias.trim() === ''){
		alert('Please enter the required fields');
		return;
	  }
	  const formData =  new FormData();

	  	formData.append('username', username);
		formData.append('email', email);
		formData.append('password', password);
		formData.append('password2', password);

	  const backendURL = 'http://localhost:8000/register/';

	  fetch(backendURL, {
		method: 'POST',
		body: formData
	  })
	  .then(response => {
		if (response.ok) {
		  return response.json();
		} else {
		  throw new Error('Network response was not ok.');
		}
	  })
	  .then(data => {
		const token = data.token;
		const id = data.user.id;
		localStorage.setItem('Token', token);
		localStorage.setItem('id', id);
		navigate(`/dashboard/${id}/`);
	  })
	  .catch(error => {
		console.error('Fehler beim Senden der Registrierungsdaten:', error);
		alert('Es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.');
	  });
  };
  

  const handleBack = () => {
	if (registering === true) {
		setRegistering(false);
		return
	}
    navigate('/');
  };
	return (
		<div className='container'>
			<label>
				Username:<br />
				<input type="text" value={username} onChange={handleUsernameChange} />
			</label>
			<br />
			<label>
				Password:<br />
				<input type="password" value={password} onChange={handlePasswordChange} />
			</label>
			<br />
			{!registering && ( <div>
			<button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} onClick={handleLogin}>Login</button>
			
			<button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} onClick={() => setRegistering(true)}>Register</button>
			</div>)}
			{registering && ( <div>
				<label>
				Email:<br />
				<input type="email" value={email} onChange={handleEmailChange} />
			</label>
			<br />
			<label>
				Alias:<br />
				<input type="alias" value={alias} onChange={handleAliasChange} />
			</label>
			<br />
				<button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} onClick={handleRegister}>complete register</button> </div>)}
			<button  className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}}onClick={handleBack}>Back</button>
		</div>
	);
}

export default Login;

