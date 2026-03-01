## Overview of system architecture

### Frontend (Next.js/React)

- The user is able to interact with the frontend through an easy React and Next.js interface. The frontend contains game lists, player props, details, standings, and more.
- The frontend then connects to the backend through an HTTP request and WebSockets for the live updates.

### Backend (FastAPI):

- The FastAPI is able to serve the REST API endpoints for all of the information such as the games, players, and standings.
- The FastAPI manages the WebSockets which is in charge of the live updates for both per game and dashboard views.
- Also utilizes NBA and ESPN APIs to pull in the integral information.

### Database:

- Through render, we utilize a PostGreSQL database to store all of the important information such as history of games, etc.

### ML Models:

- We utilized python scripts on Jupyter Notebook for the training and testing of the models as well as importing models
- The backend pulls from the models to get the probabilities.

## Summary of important team decisions

- Next.js (React) for the frontend, for server side rendering, as well as simple deployment for easy testing
- FastAPI for backend functionalities. Simple Websocket integrations for backend workflow.
- Live updates were implemented through WebSockets for the real-time experience
- Utilizing only the ESPN API rather than using the NBA API due to instability of the NBA API and inconsistency.
- Render used to deploy the backend and Vercel for frontend deployment
- Render used to deploy the PostGreSQL database for real time updates and easy connection between the backend and the database.

## UX considerations

### User Flow: 

- The User is first taken to the homepage where they are able to see the list of games
- The User is able to click a game to view the details of the game such as the stats, score, and the win probabilities.
- The main page updates in real-time with the probabilities changing every 5 seconds.
- The User is also able to navigate to the standings as well as player props
