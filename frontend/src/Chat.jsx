import React, { useState, useEffect, useRef } from 'react';
import { ListGroup, ListGroupItem, Button } from 'react-bootstrap';
import { BrowserRouter as useNavigate } from 'react-router-dom';

const Chat = (props) => {
	const [message, setMessage] = useState('');
	const [socket, setSocket] = useState(null);
	const [selectedFriend, setSelectedFriend] = useState(null);
	const [chatData, setChatData] = useState(null);
	const navigate = useNavigate();
	const backendURL = 'https://localhost/api/chats/'
	const [notification, setNotification] = useState(null);
	const messagesEndRef = useRef(null);
	const {notesocket} = props;

	useEffect(() => {
	  if (notesocket == null) return;
	  notesocket.onmessage = (event) => {
		const data = JSON.parse(event.data);
		console.log(data);
		setNotification(data);
		setTimeout(() => {
		  setNotification(null);
		}, 5000);
	  };
	}, [notesocket]);

	const scrollToBottom = () => {
	messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
	}

	useEffect(scrollToBottom, [selectedFriend]);

	const handleSendMessage = () => {
		if (message !== '') {
		  if (socket && socket.readyState === WebSocket.OPEN) {
			socket.send(JSON.stringify({ message: message }));
			setMessage('');
		  } else {
			console.error('Cannot send message, WebSocket connection is not open');
		  }
		}
	  };
	
	const reloadData = () => {
		fetch(backendURL, {
			method: 'GET',
			headers: {
			  'Content-Type': 'application/json',
			  'Authorization': `Token ${localStorage.getItem('Token')}`
			},
		  })
		  .then(response => response.json())
		  .then(data => {
			setChatData(data);
			if (selectedFriend) {
				const sameFriend = data.find(friend => friend.id === selectedFriend.id);
				setSelectedFriend(sameFriend);
			  }
		  })
		  .catch((error) => {
			console.error('Error:', error);
		  });

	};

	useEffect(() => {
		fetch(backendURL, {
		  method: 'GET',
		  headers: {
			'Content-Type': 'application/json',
			'Authorization': `Token ${localStorage.getItem('Token')}`
		  },
		})
		.then(response => response.json())
		.then(data => {
		  setChatData(data);
		})
		.catch((error) => {
		  console.error('Error:', error);
		});
	  }, []);
	  
	useEffect(() => {
		if (socket) {
		  socket.close();
		}
		if (selectedFriend) {
		  const newSocket = new WebSocket('wss://localhost/ws/chat/' + selectedFriend.participant2.id + '/?token=' + localStorage.getItem('Token'));
		  newSocket.addEventListener('open', (event) => {
			console.log('Server connection opened');
		  });
		  newSocket.addEventListener('message', (event) => {
			reloadData();
		  });
		  newSocket.addEventListener('close', (event) => {
			console.log('Server connection closed: ', event.code);
		  });
		  newSocket.addEventListener('error', (event) => {
			console.error('WebSocket error: ', event);
		  });
		  setSocket(newSocket);
		}
	  }, [selectedFriend]);

	const handleFriendClick = (chat) => {
		setSelectedFriend(chat);
	  };

	const backtoMenu = () => {	
		if (socket) {
			socket.close();
		  }
		navigate(`/dashboard/${localStorage.getItem('id')}/`);
	  };

	const handleInviteClick = (friend) => {
		const backURL = 'https://localhost/api/game-invites/create/';

		fetch(backURL, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			  'Authorization': `Token ${localStorage.getItem('Token')}`
			},
			body: JSON.stringify({ 'to_user': friend.id }),
		})
			.then(response => response.json())
			.then(data => {
			})
			.catch((error) => {
			console.error('Error:', error);
			});
		localStorage.setItem('friendID', friend.id);
		navigate(`/OnlineGame/`);
	  };

	const handleBlockUser = (friend) => {
		const backURL = 'https://localhost/api/users/' + friend.id + '/block';
		fetch(backURL, {	
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Token ${localStorage.getItem('Token')}`
			},
		})
		.then(response => response.json())
		.then(data => {	
		})
		.catch((error) => {
			console.error('Error:', error);
		});

	  }

	return (
		<div className="row">
		  <div className="col-md-4">
		  {notification && (
			<div className="notification" style={{position: 'fixed', top: '0', right: '0', backgroundColor: 'lightblue', padding: '10px'}}>
				{notification.message}
			</div>
			)}
		  <button className="btn btn-secondary mb-2" style={{ height:'30px', backgroundColor: '#000000', color: '#ffffff'}}onClick={backtoMenu}>back to profile</button>
			<h3>friends</h3>
			<ListGroup>
				{chatData ? chatData.map((chat, index) => (
					<ListGroupItem 
					key={index} 
					onClick={() => handleFriendClick(chat)}
					style={selectedFriend && selectedFriend.participant2.username === chat.participant2.username ? { backgroundColor: '#000000', color: '#ffffff' } : {}}
					>
					{chat.participant2.username}
					<Button variant="primary" className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}}onClick={(e) => {e.stopPropagation(); handleInviteClick(chat.participant2);}}>invite to a game</Button>
					<Button variant="primary" className="btn btn-secondary mb-2" style={{ height:'25px', backgroundColor: '#000000', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center'}}onClick={(e) => {e.stopPropagation(); handleBlockUser(chat.participant2);}}>block user</Button>
					</ListGroupItem>
				)) : "Loading..."}
				</ListGroup>
		  </div>
		  <div className="col-md-8">
		
			{selectedFriend && (
				<div style={{ marginTop: '85px' }}> 	
				<div style={{ height: '600px', overflow: 'auto'}}>
					{
					selectedFriend.messages.map((message, index) => (
						<p key={index}>{message.text}</p>
					))}
					<div ref={messagesEndRef} />
				</div>
				<div >
				<input style={{ width: '60%' }}
					type="text"
					value={message}
					onChange={e => setMessage(e.target.value)}
				/>
				 <button className="btn btn-secondary mb-2" style={{ height:'30px', backgroundColor: '#000000', color: '#ffffff'}}onClick={handleSendMessage}>Send</button>
				</div>
				</div>
			)}
			</div>
		</div>
	  );
};

export default Chat;

