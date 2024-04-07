import React, { useState, useEffect, useRef } from 'react';
import { ListGroup, ListGroupItem, Button } from 'react-bootstrap';
/* eslint-disable */
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';

const Chat = () => {
	const [message, setMessage] = useState('');
	const [socket, setSocket] = useState(null);
	const [selectedFriend, setSelectedFriend] = useState(null);
	const [chatData, setChatData] = useState(null);
	const navigate = useNavigate();
	const backendURL = 'http://localhost:8000/chats/'

	const messagesEndRef = useRef(null);

	const scrollToBottom = () => {
	messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
	}

	useEffect(scrollToBottom, [selectedFriend]);

	const handleSendMessage = () => {
		if (message !== '') {
		  // Check if the WebSocket connection is open
		  if (socket && socket.readyState === WebSocket.OPEN) {
			// Send the message
			socket.send(JSON.stringify({ message: message }));
	  
			// Clear the message input
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
			  'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
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
			'Authorization': `Token ${localStorage.getItem('Token')}` // Include the token in the Authorization header
		  },
		})
		.then(response => response.json())
		.then(data => {
		  setChatData(data);
		})
		.catch((error) => {
		  console.error('Error:', error);
		});
	  }, []); // Empty array means this effect runs once on mount
	  
	  useEffect(() => {
		// Close the previous WebSocket connection
		if (socket) {
		  socket.close();
		}
	  
		// Open a new WebSocket connection
		if (selectedFriend) {
		  const newSocket = new WebSocket('ws://localhost:8000/ws/chat/' + selectedFriend.participant2.id + '/?token=' + localStorage.getItem('Token'));
		  
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
		const backURL = 'http://localhost:8000/game-invites/create/';

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


	  return (
		<div className="row">
		  <div className="col-md-4">
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

