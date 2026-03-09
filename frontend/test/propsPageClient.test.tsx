///<reference types="jest" />

import { act, render, screen, waitFor } from "@testing-library/react";
import PropsPageClient from "../src/app/props/PropsPageClient";

jest.mock("next/image", () => ({
  __esModule: true,
  default: ({ unoptimized, ...props }: any) => <img {...props} />,
}));

const replaceMock = jest.fn();
const pathnameMock = "/props";
const searchParamsMock = new URLSearchParams("");

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => pathnameMock,
  useSearchParams: () => searchParamsMock,
}));

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;

  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: ((ev: any) => void) | null = null;
  onclose: (() => void) | null = null;
  readyState = MockWebSocket.OPEN;
  sentMessages: string[] = [];

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 0);
  }

  send(message: string) {
    this.sentMessages.push(message);
  }

  close() {
    if (this.onclose) this.onclose();
  }
}

describe("PropsPageClient", () => {
  beforeEach(() => {
    replaceMock.mockReset();
    MockWebSocket.instances = [];
    (global as any).WebSocket = MockWebSocket as any;
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        updated_at: "2026-03-09T00:00:00Z",
        projections: [
          {
            game_id: "401",
            player_id: "1",
            espn_player_id: "1",
            player_name: "Alpha Guard",
            team_abbr: "LAL",
            opponent_abbr: "DEN",
            is_starter: true,
            projected_pts: 25.2,
            projected_reb: 5.1,
            projected_ast: 6.4,
            source: "model",
          },
        ],
      }),
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
    delete (global as any).WebSocket;
    delete (global as any).fetch;
  });

  it("loads initial props, subscribes to props topic, handles updates, and cleans up", async () => {
    const { unmount } = render(<PropsPageClient />);

    await waitFor(() => {
      expect(screen.getByText("Alpha Guard")).toBeInTheDocument();
    });

    expect(MockWebSocket.instances.length).toBe(1);
    const ws = MockWebSocket.instances[0];

    await waitFor(() => {
      expect(ws.sentMessages).toContain(
        JSON.stringify({ action: "subscribe", topic: "props" }),
      );
    });

    act(() => {
      ws.onmessage &&
        ws.onmessage({
          data: JSON.stringify({ ok: true, action: "subscribe", topic: "props" }),
        });
    });

    expect(screen.getByText("Alpha Guard")).toBeInTheDocument();

    act(() => {
      ws.onmessage &&
        ws.onmessage({
          data: JSON.stringify({
            updated_at: "2026-03-09T00:00:30Z",
            projections: [
              {
                game_id: "401",
                player_id: "2",
                espn_player_id: "2",
                player_name: "Bravo Wing",
                team_abbr: "DEN",
                opponent_abbr: "LAL",
                is_starter: false,
                projected_pts: 18.1,
                projected_reb: 7.7,
                projected_ast: 3.2,
                source: "model",
              },
            ],
          }),
        });
    });

    await waitFor(() => {
      expect(screen.getByText("Bravo Wing")).toBeInTheDocument();
    });
    expect(screen.queryByText("Alpha Guard")).not.toBeInTheDocument();

    unmount();
    expect(ws.sentMessages).toContain(
      JSON.stringify({ action: "unsubscribe", topic: "props" }),
    );
  });
});
