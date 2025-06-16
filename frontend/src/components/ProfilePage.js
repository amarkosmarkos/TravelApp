// src/components/ProfilePage.js
import React, { useState, useEffect } from "react";
import axios from "axios";

const ProfilePage = () => {
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    // Función para obtener los datos del usuario
    const fetchUserData = async () => {
      const token = localStorage.getItem("token"); // Obtenemos el token del localStorage
      if (token) {
        try {
          const response = await axios.get("http://localhost:8000/api/users/profile", {
            headers: { Authorization: `Bearer ${token}` }, // Enviamos el token en los headers
          });
          setUserData(response.data); // Guardamos los datos del usuario en el estado
        } catch (err) {
          setError("Error fetching user data");
        }
      } else {
        setError("No token found");
      }
    };

    fetchUserData(); // Llamamos a la función para obtener los datos del usuario
  }, []);

  if (error) {
    return <div>{error}</div>; // Mostramos un mensaje de error si no se pudo obtener los datos
  }

  if (!userData) {
    return <div>Loading...</div>; // Mostramos un mensaje de carga mientras se obtienen los datos
  }

  return (
    <div>
      <h1>User Profile</h1>
      <p><strong>Name:</strong> {userData.name}</p>
      <p><strong>Email:</strong> {userData.email}</p>
    </div>
  );
};

export default ProfilePage;
