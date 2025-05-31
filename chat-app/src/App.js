import React, { useState, useEffect } from 'react';
import { Container, Box, Typography, TextField, Button, Paper, List, ListItem, ListItemText, CircularProgress } from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);
    const newMessage = { text: inputText, isUser: true };
    setMessages([...messages, newMessage]);
    setInputText('');

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputText,
          chat_history: messages.map(msg => [msg.text, msg.isUser ? 'user' : 'assistant'])
        }),
      });

      const data = await response.json();
      setMessages(prev => [...prev, { text: data.answer, isUser: false }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { text: 'Lo siento, ha ocurrido un error. Por favor, inténtalo de nuevo.', isUser: false }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <List>
              {messages.map((message, index) => (
                <ListItem
                  key={index}
                  sx={{
                    justifyContent: message.isUser ? 'flex-end' : 'flex-start',
                    mb: 1,
                  }}
                >
                  <Paper
                    sx={{
                      p: 2,
                      bgcolor: message.isUser ? 'primary.main' : 'grey.100',
                      color: message.isUser ? 'white' : 'black',
                      borderRadius: 2,
                      maxWidth: '80%',
                    }}
                  >
                    <ListItemText primary={message.text} />
                  </Paper>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>

        <Box sx={{ display: 'flex', p: 2, bgcolor: 'background.default' }}>
          <TextField
            fullWidth
            variant="outlined"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Escribe tu mensaje..."
            disabled={isLoading}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={sendMessage}
            disabled={isLoading || !inputText.trim()}
            sx={{ ml: 2 }}
          >
            {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
          </Button>
        </Box>
      </Box>
    </Container>
  );
}

export default App;
