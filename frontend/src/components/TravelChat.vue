// Inicializar WebSocket
const initWebSocket = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      console.error('No token found')
      return
    }

    // Actualizar la URL del WebSocket para que coincida con el backend
    const wsUrl = `ws://localhost:8000/api/travels/${travelId}/ws?token=${token}`
    console.log('Connecting to WebSocket:', wsUrl)
    
    socket = new WebSocket(wsUrl)
  } catch (error) {
    console.error('Error connecting to WebSocket:', error)
  }
} 