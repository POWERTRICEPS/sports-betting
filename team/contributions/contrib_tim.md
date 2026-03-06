# Timothy Nguyen – Contribution Summary

Throughout the quarter I held a retro and scrum meetings breifly as scribe. I contributed primarily to the frontend development and real-time data integration for the sports probability application. My work focused on implementing live game updates using WebSockets, building UI components to display game information, and creating a probability visualization chart for live games. 

## Feature Development
- Implemented **real-time NBA game updates using WebSockets** in `socket.js`, `socket.ts`, enabling the frontend to receive live game data from the backend.
- Connected the **frontend socket to the backend WebSocket server** to support live updates for games.
- Created the **Game Probability Win Chart** component, changes were made in `GameProbabilityChart.jsx` and `GameProbabilityChart.tsx` to visualize win probability changes during a game.

## Frontend & UI Development
- Implemented the **GameCard component**, `GameCard.jsx`,  `GameCard.tsx` to display live game information.
- Wired **live game data into the GameCard UI** so updates from the backend appear in real time.
- Refactored the **GamesPage component** `GamesPage.jsx`, `GamesPage.tsx` to use the GameCard component and structured game data for display.
- Updated frontend API configuration to use **Render backend URLs** for game data and WebSocket connections.

## Additional Contributions
- Added project documentation such as `AI_CODING.md` and `TESTING.md`, and participated in team coordination tasks including retrospectives and scrum notes.
