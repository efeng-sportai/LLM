# SportAI React Native Frontend

React Native mobile app for querying the SportAI LLM API.

## Features

- **Sample Questions**: Tap any pre-populated question to query the LLM
- **Custom Questions**: Enter your own questions
- **JSON Response Display**: View the full API response in formatted JSON
- **Answer Display**: Clean, formatted answer text
- **Loading States**: Visual feedback while querying
- **Error Handling**: Clear error messages

## Setup

1. Install dependencies:
```bash
npm install
```

2. **IMPORTANT**: Update the API URL in `App.tsx` if needed:
   - Default: `http://192.168.1.162:5001/query` (configured for local network)
   - For iOS Simulator: Can use `http://127.0.0.1:5001/query` or `http://localhost:5001/query`
   - For physical device: Use your computer's IP address
     - Find your IP: `ifconfig` (Mac/Linux) or `ipconfig` (Windows)
     - Update `LLM_API_URL` in `App.tsx`

3. Make sure the LLM server is running on port 5001:
```bash
cd ../LLM
python3 driver.py
```

## Running the App

### iOS Simulator (Mac only)
```bash
npm run ios
```

### Android Emulator
```bash
npm run android
```

### Web Browser (for testing)
```bash
npm run web
```

### Development Server
```bash
npm start
```
Then scan the QR code with Expo Go app on your phone, or press `i` for iOS simulator, `a` for Android emulator.

## Notes

- **First Query**: May take 30 seconds to 2 minutes (LLM model loading)
- **Subsequent Queries**: Faster (model caching on backend)
- **Network**: Ensure device/emulator and computer are on the same network for physical devices
- **API Endpoint**: Configured to call `POST /query` endpoint on LLM service
- **Response Format**: Displays JSON response with `question`, `answer`, and `debug` information

## Features

- **Sample Questions**: Pre-populated questions for quick testing
- **Custom Questions**: Enter your own questions via text input
- **Loading States**: Visual feedback during API calls
- **Error Handling**: Displays error messages if API call fails
- **JSON Display**: Shows full API response in formatted JSON
- **Answer Display**: Clean, readable answer text

