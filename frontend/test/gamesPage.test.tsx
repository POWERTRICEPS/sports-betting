///<reference types="jest" />

import { render, screen } from "@testing-library/react";
import GamesPage from "../src/app/page";
import { useGameData } from "../src/app/GameDataProvider";

jest.mock("../src/app/GameDataProvider", () => ({
  useGameData: jest.fn(),
}));

jest.mock("../src/app/games/GameCard", () => ({
  __esModule: true,
  default: ({ data }: any) => <div>{`Game ${data.game_id}`}</div>,
}));

jest.mock("../src/app/standings/Standings", () => ({
  __esModule: true,
  default: () => <div>Standings</div>,
}));

jest.mock("../src/app/components/DateNav", () => ({
  __esModule: true,
  default: () => <div>DateNav</div>,
}));

describe("GamesPage", () => {
  const useGameDataMock = useGameData as jest.Mock;

  beforeEach(() => {
    useGameDataMock.mockReset();
    localStorage.clear();
  });

  it("shows skeletons while games are loading", () => {
    useGameDataMock.mockReturnValue({
      games: [],
      gamesLoading: true,
      status: "connecting",
      error: null,
      reconnect: jest.fn(),
      standings: null,
      standingsLoading: false,
    });

    render(<GamesPage />);

    expect(screen.getAllByTestId("game-card-skeleton").length).toBeGreaterThan(0);
  });

  it("shows empty state when no games are available after load", () => {
    useGameDataMock.mockReturnValue({
      games: [],
      gamesLoading: false,
      status: "connected",
      error: null,
      reconnect: jest.fn(),
      standings: null,
      standingsLoading: false,
    });

    render(<GamesPage />);

    expect(screen.getByText("No games available today.")).toBeInTheDocument();
  });

  it("shows game cards when games are available", () => {
    useGameDataMock.mockReturnValue({
      games: [{ game_id: "401", status: "Final" }],
      gamesLoading: false,
      status: "connected",
      error: null,
      reconnect: jest.fn(),
      standings: null,
      standingsLoading: false,
    });

    render(<GamesPage />);

    expect(screen.getByText("Game 401")).toBeInTheDocument();
  });
});
