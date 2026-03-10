///<reference types="jest" />

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import GamesByDate from "../src/app/on/[id]/gamesByDate";

jest.mock("../src/app/games/GameCard", () => ({
  __esModule: true,
  default: ({ data }: any) => <div>{`Game ${data.game_id}`}</div>,
}));

jest.mock("../src/app/standings/Standings", () => ({
  __esModule: true,
  default: () => <div>Standings</div>,
}));

jest.mock("@/app/components/DateNav", () => ({
  __esModule: true,
  default: () => <div>DateNav</div>,
}));

describe("GamesByDate", () => {
  afterEach(() => {
    jest.resetAllMocks();
    delete (global as any).fetch;
  });

  it("shows loading skeletons while fetching games", () => {
    (global as any).fetch = jest.fn(
      () =>
        new Promise(() => {
          // keep pending
        }),
    );

    render(<GamesByDate id="20260309" />);

    expect(screen.getAllByTestId("game-card-skeleton").length).toBeGreaterThan(0);
  });

  it("shows empty state when fetch succeeds with no games", async () => {
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });

    render(<GamesByDate id="20260309" />);

    await waitFor(() => {
      expect(
        screen.getByText("No games available for this date."),
      ).toBeInTheDocument();
    });
  });

  it("shows error and retries successfully", async () => {
    (global as any).fetch = jest
      .fn()
      .mockRejectedValueOnce(new Error("boom"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ game_id: "555" }],
      });

    render(<GamesByDate id="20260309" />);

    await waitFor(() => {
      expect(
        screen.getByText("Failed to load games for this date."),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(screen.getByText("Game 555")).toBeInTheDocument();
    });
  });
});
