-- This is a table to store the user information (could add more attributes)
CREATE TABLE user_info (
    user_id INT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    user_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Table for showing the players' overall stats and not just for that specific game
CREATE TABLE player_overall_info (
    player_id INT PRIMARY KEY,
    player_name VARCHAR(50) NOT NULL,
    team VARCHAR(50),
    player_position VARCHAR(50),
    player_age INT,
    player_height VARCHAR(50),
    ppg FLOAT,
    rpg FLOAT,
    apg FLOAT,
    spg FLOAT,
    bpg FLOAT,
    fg_percentage FLOAT,
    three_pt_percentage FLOAT,
    ft_percentage FLOAT
);
-- Table to hold info for the current game
CREATE TABLE current_game_info (
    game_id INT PRIMARY KEY,
    game_date DATE NOT NULL,
    home_team VARCHAR(50) NOT NULL,
    home_team_score INT NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    away_team_score INT NOT NULL,
    game_time_elapsed TIME NOT NULL,
    game_stadium VARCHAR(50),
    home_win_probability FLOAT,
    away_win_probability FLOAT,
    probability_last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE past_game_info (
    past_game_id INT PRIMARY KEY,
    game_date DATE NOT NULL,
    home_team VARCHAR(50) NOT NULL,
    home_team_score INT NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    away_team_score INT NOT NULL,
    game_stadium VARCHAR(50),
    home_win_probability FLOAT,
    away_win_probability FLOAT,
    probability_last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Detailed stats for completed games (matches full game payload: team identity, records, quarters, leaders, totals, L10, status).
CREATE TABLE past_game_stats (
    past_game_id INT PRIMARY KEY REFERENCES past_game_info(past_game_id) ON DELETE CASCADE,
    status VARCHAR(50),
    home_team VARCHAR(100),
    home_city VARCHAR(100),
    home_abbreviation VARCHAR(10),
    home_wins INT,
    home_losses INT,
    home_score INT,
    away_team VARCHAR(100),
    away_city VARCHAR(100),
    away_abbreviation VARCHAR(10),
    away_wins INT,
    away_losses INT,
    away_score INT,
    home_q1 FLOAT,
    home_q2 FLOAT,
    home_q3 FLOAT,
    home_q4 FLOAT,
    away_q1 FLOAT,
    away_q2 FLOAT,
    away_q3 FLOAT,
    away_q4 FLOAT,
    home_leader_pts_name VARCHAR(100),
    home_leader_pts_val VARCHAR(20),
    home_leader_reb_name VARCHAR(100),
    home_leader_reb_val VARCHAR(20),
    home_leader_ast_name VARCHAR(100),
    home_leader_ast_val VARCHAR(20),
    away_leader_pts_name VARCHAR(100),
    away_leader_pts_val VARCHAR(20),
    away_leader_reb_name VARCHAR(100),
    away_leader_reb_val VARCHAR(20),
    away_leader_ast_name VARCHAR(100),
    away_leader_ast_val VARCHAR(20),
    home_reb VARCHAR(20),
    home_ast VARCHAR(20),
    home_fgm VARCHAR(20),
    home_fga VARCHAR(20),
    home_ftm VARCHAR(20),
    home_fta VARCHAR(20),
    home_points VARCHAR(20),
    home_3pa VARCHAR(20),
    home_3pm VARCHAR(20),
    away_reb VARCHAR(20),
    away_ast VARCHAR(20),
    away_fgm VARCHAR(20),
    away_fga VARCHAR(20),
    away_ftm VARCHAR(20),
    away_fta VARCHAR(20),
    away_points VARCHAR(20),
    away_3pa VARCHAR(20),
    away_3pm VARCHAR(20),
    home_l10_wins INT,
    away_l10_wins INT
);

-- Table to store historical probability calculations (every 5 seconds during the game)
-- This table tracks ALL probability calculations for both current and past games
CREATE TABLE game_probability_history (
    probability_id SERIAL PRIMARY KEY,
    game_id INT NOT NULL,
    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    game_time_elapsed TIME NOT NULL,
    quarter INT,
    home_team_score INT NOT NULL,
    away_team_score INT NOT NULL,
    home_win_probability FLOAT NOT NULL,
    away_win_probability FLOAT NOT NULL,
    llm_model_version VARCHAR(50)
);

-- Index for efficient querying of probability history by game and time
CREATE INDEX idx_game_timestamp ON game_probability_history(game_id, calculation_timestamp);

-- Table to hold info for the players that are currently playing in the game
CREATE TABLE player_in_game_info (
    player_in_game_id INT PRIMARY KEY,
    player_id INT REFERENCES player_overall_info(player_id),
    game_id INT REFERENCES current_game_info(game_id),
    game_date DATE NOT NULL,
    points_total INT,
    rebounds INT,
    assists INT,
    steals INT,
    blocks INT,
    minutes_played INT,
    fg_made INT,
    fg_attempted INT
);