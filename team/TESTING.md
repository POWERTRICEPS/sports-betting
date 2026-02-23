# Testing Demo: Jest

When designing a unit test, we decided to use Jest. This is because research showed that Jest was the most documented and was recommended in past offerings of CS 148.

## Units to Test: useGameData

We decided to test our useGameData implementation. useGameData connects to a websocket from our backend and receives updates on all current gamestates. It then passes these updates to the game components to create a realtime updating display. We thought it best to test this to ensure that the websocket was handling connections gracefully and that it was able to process both good and bad data accordingly. 

## Testing Implementation 

We wrote 3 unit tests for this file. One to test live updates, one to test websocket errors, and one to test http errors. To do this, we needed to create a mock websocket that would send data in a predictable yet stable pattern to assert that it worked. We also created a non-opening mock websocket to demonstrate what would happen if the websocket connection never happened. 

## Result
We ensured these unit tests passed to assert our implementation worked. 

# Higher Level Testing

## Previous Unit Testing Implementation

Last lab we implemented a single unit test for our useGameData implemenation using Jest, which allowed us to ensure that the websocket used for updating our game data was properly connecting and accepting data. The way you run this test is as follows:

```bash
cd frontend
npm test
```

The test itself is located at:

```bash
frontend/test
```

## Unit testing going Forward

Going forward we plan on adding unit tests when we feel they are needed. As of now our rendering logic is very simple and does not require large amounts of tests to maintian. However, we have thought about implemnting a few unit tests on the backend since it is more complex.

## E2E test using Playwright

For our end to end test we implemented an E2E test that simulates one of the core user functionality of our app. This test stimulates a user loading our homeepage, making sure that atleast one game card is properly rendered, clicking on that game navigating to the game page, and ensuring the page shows stats for this game.

To run this test

```bash
cd frontend
npm install
npx playwright install
npm run test:e2e
```

The test itself is located at:

```bash
frontend/e2e
```

## Higher level testing going forward

We have decided that E2E tests are very useful for us to ensure that the main functionality of our apps are working properly. Since our app has a simple render logic, E2E tests allow us to ensure that everything is working together properly and seem to work better than large amounts of unit test. Going forward we plan to impement E2E tests for core use functionality.