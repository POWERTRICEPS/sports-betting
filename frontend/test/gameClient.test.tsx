///<reference types="jest" />

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import GameClient from "../src/app/games/[id]/GameClient";

jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: any) => <img {...props} />,
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: any) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

jest.mock("../src/app/games/[id]/WinProbabilityGraph", () => ({
  __esModule: true,
  default: () => <div>WinProbGraph</div>,
}));

class MockWebSocket {
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onclose: (() => void) | null = null;

  send() {}
  close() {}
}

describe("GameClient", () => {
  beforeEach(() => {
    (global as any).WebSocket = MockWebSocket as any;
  });

  afterEach(() => {
    jest.resetAllMocks();
    delete (global as any).WebSocket;
    delete (global as any).fetch;
  });

  it("shows loading state while initial fetch is pending", () => {
    (global as any).fetch = jest.fn(
      () =>
        new Promise(() => {
          // pending fetch
        }),
    );

    render(<GameClient id="401" />);

    expect(screen.getByTestId("game-detail-loading")).toBeInTheDocument();
  });

  it("shows error state and retries successfully", async () => {
    (global as any).fetch = jest
      .fn()
      .mockRejectedValueOnce(new Error("boom"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          game_id: "401",
          status: "Final",
          home_team: "Lakers",
          home_city: "Los Angeles",
          home_abbreviation: "LAL",
          home_wins: 10,
          home_losses: 5,
          home_score: 101,
          home_q1: 20,
          home_q2: 25,
          home_q3: 30,
          home_q4: 26,
          home_leader_pts_name: null,
          home_leader_pts_val: null,
          home_leader_reb_name: null,
          home_leader_reb_val: null,
          home_leader_ast_name: null,
          home_leader_ast_val: null,
          home_reb: null,
          home_ast: null,
          home_fga: null,
          home_fgm: null,
          home_fta: null,
          home_ftm: null,
          home_points: null,
          home_3pa: null,
          home_3pm: null,
          away_team: "Warriors",
          away_city: "Golden State",
          away_abbreviation: "GSW",
          away_wins: 9,
          away_losses: 6,
          away_score: 99,
          away_q1: 19,
          away_q2: 20,
          away_q3: 30,
          away_q4: 30,
          away_leader_pts_name: null,
          away_leader_pts_val: null,
          away_leader_reb_name: null,
          away_leader_reb_val: null,
          away_leader_ast_name: null,
          away_leader_ast_val: null,
          away_reb: null,
          away_ast: null,
          away_fga: null,
          away_fgm: null,
          away_fta: null,
          away_ftm: null,
          away_points: null,
          away_3pa: null,
          away_3pm: null,
        }),
      });

    render(<GameClient id="401" />);

    await waitFor(() => {
      expect(screen.getByTestId("game-detail-error")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(screen.getByText("Final")).toBeInTheDocument();
      expect(screen.getByText("WinProbGraph")).toBeInTheDocument();
    });
  });
});
