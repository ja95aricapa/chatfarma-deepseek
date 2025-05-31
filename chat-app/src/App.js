import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Snackbar,
  Alert
} from '@mui/material';
import { Send as SendIcon, UploadFile as UploadFileIcon } from '@mui/icons-material';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Función para mostrar notificaciones
  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  // Cerrar snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Enviar mensaje al backend (/chat)
  const sendMessage = async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);
    const newMessage = { text: inputText, isUser: true };
    setMessages((prev) => [...prev, newMessage]);
    setInputText('');

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: inputText,
          chat_history: messages.map((msg) => [msg.text, msg.isUser ? 'user' : 'assistant'])
        }),
      });
      const data = await response.json();
      setMessages((prev) => [...prev, { text: data.answer, isUser: false }]);
    } catch (error) {
      console.error('Error /chat:', error);
      setMessages((prev) => [
        ...prev,
        { text: 'Lo siento, ocurrió un error al consultar el servidor.', isUser: false }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Llamar a /train para indexar toda la carpeta data_to_train/
  const handleTrain = async () => {
    setIsTraining(true);
    try {
      const res = await fetch('http://localhost:8000/train', { method: 'POST' });
      const data = await res.json();
      showSnackbar(data.message, data.status === 'success' ? 'success' : 'warning');
    } catch (err) {
      console.error('Error /train:', err);
      showSnackbar('Error al ejecutar /train', 'error');
    } finally {
      setIsTraining(false);
    }
  };

  // Subir historia clínica a /upload_patient
  const handleUploadPatient = async () => {
    if (!uploadFile) {
      showSnackbar('Selecciona un archivo primero', 'warning');
      return;
    }
    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const res = await fetch('http://localhost:8000/upload_patient', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      showSnackbar(data.message, data.status === 'success' ? 'success' : 'error');
      // Limpiar el input de archivo
      setUploadFile(null);
      document.getElementById('patient-file-input').value = null;
    } catch (err) {
      console.error('Error /upload_patient:', err);
      showSnackbar('Error al subir historia clínica', 'error');
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* TÍTULO y acción de entrenamiento */}
        <Typography variant="h4" gutterBottom>
          FarmaAsisChat
        </Typography>
        <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            onClick={handleTrain}
            disabled={isTraining}
          >
            {isTraining ? <CircularProgress size={20} /> : 'Actualizar conocimientos'}
          </Button>
          <label htmlFor="patient-file-input">
            <input
              id="patient-file-input"
              type="file"
              accept=".pdf,.docx,.doc,.xlsx,.xls,.png,.jpg,.jpeg"
              style={{ display: 'none' }}
              onChange={(e) => setUploadFile(e.target.files[0])}
            />
            <Button
              variant="outlined"
              startIcon={<UploadFileIcon />}
              component="span"
            >
              {uploadFile ? uploadFile.name : 'Seleccionar historia clínica'}
            </Button>
          </label>
          <Button
            variant="contained"
            color="secondary"
            onClick={handleUploadPatient}
            disabled={!uploadFile}
          >
            Subir historia clínica
          </Button>
        </Box>

        {/* Área de conversación */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}>
          <Paper sx={{ p: 2, height: '100%', bgcolor: '#fafafa' }}>
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

        {/* Input y botón de enviar */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            variant="outlined"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Escribe tu pregunta..."
            disabled={isLoading}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={sendMessage}
            disabled={isLoading || !inputText.trim()}
          >
            {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
          </Button>
        </Box>
      </Box>

      {/* Snackbar para notificaciones */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default App;
