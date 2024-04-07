import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardTitle} from 'react-bootstrap';
/* eslint-disable */
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';

const Dashboard = (props) => {
  const [userData, setUserData] = useState(null); // Zustand für Benutzerdaten
  let { id } = useParams();
  const navigate = useNavigate();
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [notification, setNotification] = useState(null);
  const [newProfileData, setNewProfileData] = useState({
    image: '',
    username: '',
    email: '',
    password: '',
  });
  const {socket} = props;

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
    if (userData) {
      setNewProfileData({
        image: userData.profile.image,
        username: userData.username,
        email: userData.email,
        password: '',
      });
    }
  }, [userData]);

  const handleProfileDataChange = (event) => {
    if (event.target.name === 'image') {
      setNewProfileData({
        ...newProfileData,
        [event.target.name]: event.target.files[0],
      });
    } else {
      setNewProfileData({
        ...newProfileData,
        [event.target.name]: event.target.value,
      });
    }
  };

  const handleProfileUpdate = () => {
    const formData = new FormData();
    for (const key in newProfileData) {
      if (newProfileData[key] !== '') {
        formData.append(key, newProfileData[key]);
      }
    }
  
    fetch(`http://localhost:8000/users/${userData.id}/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Token ${localStorage.getItem('Token')}`,
      },
      body: formData,
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (data) {
          setUserData(data);
          setIsEditingProfile(false);
        } else {
          throw new Error('Invalid data');
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        alert('Error:', error.message);
      });
  };

  function fetchUserData() {
    const backendURL = 'http://localhost:8000/users/';
    const userId = localStorage.getItem('id');
  
    if (!userId) {
      console.error('Benutzer-ID nicht im localStorage gefunden');
      return;
    }
  
    const requestURL = `${backendURL}${userId}/`;
  
    fetch(requestURL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
      },
    })
    .then(response => response.json())
    .then(data => {
      setUserData(data);
    })
    .catch((error) => {
      console.error('Error:', error);
    });
  }
  
  useEffect(() => {
    const backendURL = 'http://localhost:8000/users/';
    const userId = localStorage.getItem('id');
    

    if (!userId) {
      console.error('Benutzer-ID nicht im localStorage gefunden');
      return;
    }

    const requestURL = `${backendURL}${id}/`;

    fetch(requestURL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
      },
    })
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error('Es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.');
      }
    })
    .then(data => {
      setUserData(data); // Benutzerdaten im Zustand speichern
    })
    .catch(error => {
      console.error('Fehler beim Senden der Registrierungsdaten:', error);
      alert(error.message);
    });
  }, [id]);

  function addFriend() {
    fetch('http://localhost:8000/friend-requests/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
      },
      body: JSON.stringify({
        'from_user': parseInt(localStorage.getItem('id'), 10),
        'to_user': userData.id,
      }),
    })
    .then(response => response.json())
    .then(data => {
      
      console.log('Success:', data);
      console.log(localStorage.getItem('id'));
      console.log(localStorage.getItem('Token'));
      console.log(userData.id);
      window.location.reload();
    })
    .catch((error) => {
      console.error('Error:', error);
    });
  }

  function acceptFriendRequest(requestId) {


    fetch(`http://localhost:8000/friend-requests/${requestId}/accept/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application  /json',   
        'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header  
      },  
    })
    fetchUserData();
    window.location.reload();


    // Send a request to the backend to accept the friend request
    // Then fetch the userData again to update the list of friend requests
  }
  const handleBack = () => {
  
     
      navigate('/'); // Navigiere zur Startseite, wenn der "Zurück"-Button geklickt wird
      window.location.reload();
    };
  
    const handleOut = () => {
      localStorage.removeItem('Token'); 
      localStorage.removeItem('id');
      navigate('/'); // Navigiere zur Startseite, wenn der "Zurück"-Button geklickt wird
      window.location.reload();
    };

    const changeProfil = () => {
      if (isEditingProfile) {
        setIsEditingProfile(false);
        return;
      }
      setIsEditingProfile(true);
    };

    const handleChat = () => {
      navigate(`/Chat`);
    };

    const acceptInvite = (inviteId) => {

      localStorage.setItem('friendID', inviteId.from_user_id);
      const backendURL = `http://localhost:8000/game-invites/delete/${inviteId.id}/`;
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
		  navigate(`/OnlineGame/`);
    };

    const declineInvite = (inviteId) => {
      const backendURL = `http://localhost:8000/game-invites/delete/${inviteId.id}/`;
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
      
    };
    
    return (
      <div className="container mt-5">
        {notification && <div className="notification" style={{position: 'fixed', top: 0, right: 0, backgroundColor: 'lightblue', padding: '10px'}}>{notification.message}</div>}
        {userData && !isEditingProfile ? (
          <>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexDirection: 'row', height: '100vh'}}>
            <Card style={{ flex: '1', width: '30vw', paddingTop: '1rem', maxHeight: '50vh'}}>
              
              <Card.Body style={{ overflow: 'auto', maxHeight: '100%'}}>
              <Card.Img variant="top" src={userData.profile.image} style={{ objectFit: 'contain', maxHeight: '50%' }} />
                <Card.Title>{userData.username}</Card.Title>
                {userData.profile.is_online ? 'Online' : 'Offline'}
                <Card.Text>
                  Email: {userData.email} <br />
                  Games Won: {userData.profile.games_won} Games Lost: {userData.profile.games_lost}
                </Card.Text>
              </Card.Body>
              </Card>
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <Card style={{ flex: '1', width: '30vw', paddingTop: '1rem', maxHeight: '50%'}}>
              <CardTitle>Friends</CardTitle>
              <Card.Body style={{ overflow: 'auto', maxHeight: '100%'}}>
                <ul>
                {userData.profile.friends.map((friend, index) => (
                  <li key={index}>
                    <a href={`/dashboard/${friend.id}`}>{friend.username}</a>
                  </li>
                ))}
              </ul>
                {!userData.profile.is_current_user && !userData.profile.already_sent_request && <button className="btn btn-primary m-1" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}} onClick={addFriend}>Add Friend</button>}
                {userData.profile.is_current_user && <div>Friend Requests:
              <ul>
                {userData.profile.to_user.map((request, index) => (
                  <li key={index}>
                    {request.from_user_username}
                    <button className="btn btn-primary m-1" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}} onClick={() => acceptFriendRequest(request.id)}>Accept</button>
                  </li>
                ))}
              </ul></div>}
              </Card.Body>
              </Card>
              {userData.profile.is_current_user && (
              <Card style={{ flex: '1', width: '30vw', paddingTop: '1rem'}}>
                <CardTitle>Game Invites</CardTitle>
                <Card.Body style={{ overflow: 'auto', maxHeight: '100%'}}>
                  <div >
                    {userData.profile.game_invites_received.map((invite, index) => (
                      <div key={index}>
                        <Card.Text>
                          From: {invite.from_user} <br />
                          Date: {new Date(invite.created).toLocaleString()}
                        </Card.Text>
                        <button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} onClick={() => acceptInvite(invite)}>Accept</button>
                        <button className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}} onClick={() => declineInvite(invite)}>Decline</button>
                      </div>
                    ))}
                  </div>
                </Card.Body>
              </Card>
              )}
              </div>
              <Card style={{ flex: '1', width: '30vw', paddingTop: '2rem'}}>
                <CardTitle>Game History</CardTitle>
                <Card.Body style={{ overflow: 'auto', maxHeight: '100%', display: 'flex', flexDirection: 'column' }}>
                <ul style={{ flex: 1, display: 'flex', flexDirection: 'column', width: '100%' }}>
                  {userData.profile.games.map((game, index) => (
                    <li key={index} style={{ flex: 1, width: '100%' }}>
                      {new Date(game.created).toLocaleString()} | vs <a href={`/dashboard/${game.opponent_id}`}>{game.opponent_username}</a> | {game.p1_score} : {game.p2_score} {game.is_winner ? 'won' : 'lost'}
                    </li>
                  ))}
                </ul>
              </Card.Body>
              
            </Card>
          </div>
            {userData.profile.is_current_user && <div> <button className="btn btn-primary m-1" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}} onClick={changeProfil}>edit profile</button></div>}
            <button className="btn btn-primary m-1" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}} onClick={handleChat}>chat</button>
            <button className="btn btn-primary m-1" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}} onClick={handleBack}>back to menu</button>
            <button className="btn btn-primary m-1" style={{width: '18rem', height: '2rem', backgroundColor: '#000000', color: '#ffffff'}} onClick={handleOut}>log out</button>
          </>
          
        ) : (
          <div className="container">
          <form>
            <div className="mb-3">
              <label className="form-label">Choose your new profile picture</label>
              <input type="file" className="form-control" name="image" onChange={handleProfileDataChange} />
            </div>
            <div className="mb-3">
              <label className="form-label">Username</label>
              <input type="text" className="form-control" name="username" value={newProfileData.username} onChange={handleProfileDataChange} />
            </div>
            <div className="mb-3">
              <label className="form-label">Email</label>
              <input type="email" className="form-control" name="email" value={newProfileData.email} onChange={handleProfileDataChange} />
            </div>
            <div className="mb-3">
              <label className="form-label">Password</label>
              <input type="password" className="form-control" name="password" value={newProfileData.password} onChange={handleProfileDataChange} />
            </div>
            <button className="btn btn-primary mb-2" style={{ height:'30px', backgroundColor: '#000000', color: '#ffffff'}} onClick={handleProfileUpdate}>update profile</button>
           
            <button className="btn btn-secondary mb-2" style={{ height:'30px', backgroundColor: '#000000', color: '#ffffff'}} onClick={changeProfil}>cancel</button>
          </form>
        </div>
        )}
      </div>
    );}

export default Dashboard;
